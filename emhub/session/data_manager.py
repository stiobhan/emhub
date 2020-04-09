# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (delarosatrevin@scilifelab.se) [1]
# *              Grigory Sharov (gsharov@mrc-lmb.cam.ac.uk) [2]
# *
# * [1] SciLifeLab, Stockholm University
# * [2] MRC Laboratory of Molecular Biology (MRC-LMB)
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'delarosatrevin@scilifelab.se'
# *
# **************************************************************************

import os
import datetime as dt
import decimal
import datetime

from sqlalchemy import (create_engine, Column, Integer, String, DateTime,
                        Boolean, Float, ForeignKey, Text, text)
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


from .session_hdf5 import H5SessionData


class SessionManager:
    """ Main class that will manage the sessions and their information.
    """
    def __init__(self, sqlitePath):
        engine = create_engine('sqlite:///' + sqlitePath,
                               convert_unicode=True,
                               echo=True)
        self._db_session = scoped_session(sessionmaker(autocommit=False,
                                                       autoflush=False,
                                                       bind=engine))
        Base = declarative_base()
        Base.query = self._db_session.query_property()

        self.__createModels(Base)

        # Create the database if it does not exists
        if not os.path.exists(sqlitePath):
            Base.metadata.create_all(bind=engine)
            # populate db with test data
            self.__populateTestData()

        self._lastSessionId = None
        self._lastSession = None

    # ------------------------- USERS ----------------------------------
    def create_user(self, **attrs):
        """ Create a new user in the DB.
        """
        attrs['created'] = dt.datetime.now()
        # FIXME, admin should be False by default
        if 'roles' not in attrs:
            attrs['roles'] = 'user'

        password = attrs['password']
        del attrs['password']
        new_user = self.User(**attrs)
        new_user.set_password(password)

        self._db_session.add(new_user)
        self._db_session.commit()

    def get_users(self, condition=None, orderBy=None, asJson=False):
        return self.__items_from_query(self.User,
                                       condition=condition,
                                       orderBy=orderBy,
                                       asJson=asJson)

    def get_user_by(self, **kwargs):
        """ This should return a single user or None. """
        return self.__item_by(self.User, **kwargs)

    # ------------------------- RESOURCES ---------------------------------
    def create_resource(self, **attrs):
        new_resource = self.Resource(**attrs)
        self._db_session.add(new_resource)
        self._db_session.commit()

    def get_resources(self, condition=None, orderBy=None, asJson=False):
        return self.__items_from_query(self.Resource,
                                       condition=condition,
                                       orderBy=orderBy,
                                       asJson=asJson)

    # ------------------------- SESSIONS ----------------------------------
    def create_booking(self, **attrs):
        new_booking = self.Booking(**attrs)
        self._db_session.add(new_booking)
        self._db_session.commit()

    def get_bookings(self, condition=None, orderBy=None, asJson=False):
        return self.__items_from_query(self.Booking,
                                       condition=condition,
                                       orderBy=orderBy,
                                       asJson=asJson)

    # ------------------------- SESSIONS ----------------------------------
    def get_sessions(self, condition=None, orderBy=None, asJson=False):
        """ Returns a list.
        condition example: text("id<:value and name=:name")
        """
        return self.__items_from_query(self.Session,
                                       condition=condition,
                                       orderBy=orderBy,
                                       asJson=asJson)

    def create_session(self, **attrs):
        """ Add a new session row. """
        new_session = self.Session(**attrs)
        self._db_session.add(new_session)
        self._db_session.commit()

    def update_session(self, sessionId, **attrs):
        """ Update session attrs. """
        session = self.Session.query.get(sessionId)

        for attr in attrs:
            session.attr = attrs[attr]

        self._db_session.commit()

    def delete_session(self, sessionId):
        """ Remove a session row. """
        session = self.Session.query.get(sessionId)
        self._db_session.delete(session)
        self._db_session.commit()

    def load_session(self, sessionId):
        if sessionId == self._lastSessionId:
            session = self._lastSession
        else:
            session = self.Session.query.get(sessionId)
            session.data = H5SessionData(session.sessionData, 'r')
            self._lastSessionId = sessionId
            self._lastSession = session

        return session

    def close(self):
        # if self._lastSession is not None:
        #     self._lastSession.data.close()

        self._db_session.remove()

    # --------------- Internal implementation methods --------------------
    def __items_from_query(self, ModelClass,
                           condition=None, orderBy=None, asJson=False):
        query = self._db_session.query(ModelClass)

        if condition is not None:
            query = query.filter(text(condition))

        if orderBy is not None:
            query = query.order_by(orderBy)

        result = query.all()
        return [s.json() for s in result] if asJson else result

    def __item_by(self, ModelClass, **kwargs):
        query = self._db_session.query(ModelClass)
        return query.filter_by(**kwargs).one_or_none()

    def __createModels(self, Base):

        def _json(obj):
            """ Return row info as json dict. """
            def jsonattr(k):
                v = getattr(obj, k)
                if isinstance(v, datetime.date):
                    return v.isoformat()
                elif isinstance(v, decimal.Decimal):
                    return float(v)
                else:
                    return v

            return {c.key: jsonattr(c.key) for c in obj.__table__.c}

        class Resource(Base):
            """ Representation of different type of Resources.
            (e.g Micrographs, other instruments or services.
            """
            __tablename__ = 'resources'

            id = Column(Integer,
                        primary_key=True)
            name = Column(String(64),
                          index=True,
                          unique=True,
                          nullable=False)

            tags = Column(String(256),
                          nullable=False)

            image = Column(String(64),
                           nullable=False)

            color = Column(String(16),
                           nullable=False)

        class User(UserMixin, Base):
            """Model for user accounts."""
            __tablename__ = 'users'

            id = Column(Integer,
                        primary_key=True)
            username = Column(String(64),
                              index=True,
                              unique=True,
                              nullable=False)
            email = Column(String(80),
                           index=False,
                           unique=True,
                           nullable=False)

            name = Column(String(256),
                          nullable=False)

            created = Column(DateTime,
                             index=False,
                             unique=False,
                             nullable=False)

            # Default role should be: 'user'
            # more roles can be comma separated: 'user,admin,manager'
            roles = Column(String(128),
                           nullable=False)

            password_hash = Column(String(256),
                                   unique=True,
                                   nullable=False)

            # one user to many sessions, bidirectional
            sessions = relationship('Session', back_populates="users")

            def set_password(self, password):
                """Create hashed password."""
                self.password_hash = generate_password_hash(password,
                                                            method='sha256')

            def check_password(self, password):
                """Check hashed password."""
                return check_password_hash(self.password_hash, password)

            def __repr__(self):
                return '<User {}>'.format(self.username)

            def json(self):
                return _json(self)

            @property
            def is_developer(self):
                return 'developer' in self.roles

            @property
            def is_admin(self):
                return 'admin' in self.roles or self.is_developer

            @property
            def is_manager(self):
                return 'manager' in self.roles or self.is_admin

            @property
            def is_pi(self):
                return 'pi' in self.roles

        class Booking(Base):
            """Model for user accounts."""
            __tablename__ = 'bookings'

            id = Column(Integer,
                        primary_key=True)

            title = Column(String(256),
                           nullable=False)

            start = Column(DateTime,
                           nullable=False)

            end = Column(DateTime,
                         nullable=False)

            # booking, slot or downtime
            type = Column(String(16),
                          nullable=False)

            description = Column(Text,
                                 nullable=True)

            resource_id = Column(Integer, ForeignKey('resources.id'))
            resource = relationship("Resource")

            creator_id = Column(Integer, ForeignKey('users.id'),
                                nullable=False)
            creator = relationship("User", foreign_keys=[creator_id])

            owner_id = Column(Integer, ForeignKey('users.id'),
                              nullable=False)
            owner = relationship("User", foreign_keys=[owner_id])

            def __repr__(self):
                return '<Booking {}>'.format(self.title)

            def json(self):
                return _json(self)

            # Following methods are required by flask-login
            # TODO: Implement flask-login required methods

        class Session(Base):
            """Model for sessions."""
            __tablename__ = 'sessions'

            id = Column(Integer,
                        primary_key=True)
            sessionData = Column(String(80),
                                 index=False,
                                 unique=True,
                                 nullable=False)
            sessionName = Column(String(80),
                                 index=True,
                                 unique=False,
                                 nullable=False)
            dateStarted = Column(DateTime,
                                 index=False,
                                 unique=False,
                                 nullable=False)
            description = Column(Text,
                                 index=False,
                                 unique=False,
                                 nullable=True)
            status = Column(String(20),
                            index=False,
                            unique=False,
                            nullable=False)
            microscope = Column(String(64),
                                index=False,
                                unique=False,
                                nullable=False)
            voltage = Column(Integer,
                             index=False,
                             unique=False,
                             nullable=False)
            cs = Column(Float,
                        index=False,
                        unique=False,
                        nullable=False)
            phasePlate = Column(Boolean,
                                index=False,
                                unique=False,
                                nullable=False)
            detector = Column(String(64),
                              index=False,
                              unique=False,
                              nullable=False)
            detectorMode = Column(String(64),
                                  index=False,
                                  unique=False,
                                  nullable=False)
            pixelSize = Column(Float,
                               index=False,
                               unique=False,
                               nullable=False)
            dosePerFrame = Column(Float,
                                  index=False,
                                  unique=False,
                                  nullable=False)
            totalDose = Column(Float,
                               index=False,
                               unique=False,
                               nullable=False)
            exposureTime = Column(Float,
                                  index=False,
                                  unique=False,
                                  nullable=False)
            numOfFrames = Column(Integer,
                                 index=False,
                                 unique=False,
                                 nullable=False)
            numOfMovies = Column(Integer,
                                 index=False,
                                 unique=False,
                                 nullable=False)
            numOfMics = Column(Integer,
                               index=False,
                               unique=False,
                               nullable=False)
            numOfCtfs = Column(Integer,
                               index=False,
                               unique=False,
                               nullable=False)
            numOfPtcls = Column(Integer,
                                index=False,
                                unique=False,
                                nullable=False)
            numOfCls2D = Column(Integer,
                                index=False,
                                unique=False,
                                nullable=False)
            ptclSizeMin = Column(Integer,
                                 index=False,
                                 unique=False,
                                 nullable=False)
            ptclSizeMax = Column(Integer,
                                 index=False,
                                 unique=False,
                                 nullable=False)

            # one user to many sessions, bidirectional
            userid = Column(Integer, ForeignKey('users.id'),
                            nullable=False)
            users = relationship("User", back_populates="sessions")

            def __repr__(self):
                return '<Session {}>'.format(self.sessionName)

            def json(self):
                return _json(self)

        self.User = User
        self.Resource = Resource
        self.Booking = Booking
        self.Session = Session

    def __populateTestData(self):
        # Create tables with test data for each database model
        print("Populating users...")
        self.__populateUsers()
        print("Populating resources...")
        self.__populateResources()
        print("Populating sessions...")
        self.__populateSessions()
        print("Populating Bookings")
        self.__populateBookings()

    def __populateUsers(self):
        # Create user table
        usernames = ['name1', 'name2', 'name3']
        emails = ['abc@def.com', 'fgh@ert.com', 'yu@dfh.com']

        """
        Petey Cruiser
        Paul Molive
        Anna Mull
        Barb Ackue
        Greta Life
        Walter Melon
        Monty Carlo
        """

        usersData = [
            ('Peter Cruiser', 'admin'),
            ('Paul Molive', 'admin,manager'),
            ('Anna Mull', 'manager'),
            ('Barb Ackue', 'manager'),
            ('Greta Life', 'user'),
            ('Walter Melon', 'user'),
            ('Monty Carlo', 'user,pi')
        ]

        for name, roles in usersData:
            first, last = name.lower().split()
            self.create_user(username=last,
                             email='%s.%s@emhub.org' % (first, last),
                             password=last,
                             name=name,
                             roles=roles)
        self._db_session.commit()

    def __populateResources(self):
        resources = [
            {'name': 'Titan Krios 1', 'tags': 'microscope krios',
             'image': 'titan-krios.png', 'color': '#3abae8'},
            {'name': 'Titan Krios 2', 'tags': 'microscope krios',
             'image': 'titan-krios.png', 'color': '#213b94'},
            {'name': 'Talos Artica', 'tags': 'microscope talos',
             'image': 'talos-artica.png', 'color': '#619e3e'},
            {'name': 'Vitrobot', 'tags': '',
             'image': 'vitrobot.png', 'color': '#9e8e3e'},
            {'name': 'Users Drop-in', 'tags': 'service',
             'image': 'users-dropin.png', 'color': 'blue'}
        ]

        for rDict in resources:
            self.create_resource(**rDict)

    def __populateBookings(self):
        now = dt.datetime.now()

        # Create a downtime from today to one week later
        self.create_booking(title='First Booking',
                            start=now.replace(day=21),
                            end=now.replace(day=28),
                            type='downtime',
                            resource_id=1,
                            creator_id=1,  # first user for now
                            owner_id=1,  # first user for now
                            description="Some downtime for some problem")

        # Create a booking at the downtime from today to one week later
        self.create_booking(title='Booking Krios 1',
                            start=now.replace(day=1, hour=9),
                            end=now.replace(day=2, hour=23, minute=59),
                            type='booking',
                            resource_id=1,
                            creator_id=2,  # first user for now
                            owner_id=2,  # first user for now
                            description="Krios 1 for user 2")
        # Create a booking at the downtime from today to one week later
        self.create_booking(title='Booking Krios 2',
                            start=now.replace(day=2, hour=9),
                            end=now.replace(day=4, hour=23, minute=59),
                            type='booking',
                            resource_id=2,
                            creator_id=1,  # first user for now
                            owner_id=3,  # first user for now
                            description="Krios 2 for user 3")

    def __populateSessions(self):
        users = [1, 2, 2]
        session_names = ['supervisor_23423452_20201223_123445',
                         'epu-mysession_20122310_234542',
                         'mysession_very_long_name']

        testData = os.environ.get('EMHUB_TESTDATA', None)
        fns = [os.path.join(testData, 'hdf5/20181108_relion30_tutorial.h5'),
               os.path.join(testData, 'hdf5/t20s_pngs.h5'), 'non-existing-file']

        scopes = ['Krios 1', 'Krios 2', 'Krios 3']
        numMovies = [423, 234, 2543]
        numMics = [0, 234, 2543]
        numCtfs = [0, 234, 2543]
        numPtcls = [0, 2, 2352534]
        status = ['Running', 'Error', 'Finished']

        for f, u, s, st, sc, movies, mics, ctfs, ptcls in zip(fns, users, session_names,
                                                              status, scopes, numMovies,
                                                              numMics, numCtfs, numPtcls):
            new_session = self.Session(
                sessionData=f,
                userid=u,
                sessionName=s,
                dateStarted=dt.datetime.now(),
                description='Long description goes here.....',
                status=st,
                microscope=sc,
                voltage=300,
                cs=2.7,
                phasePlate=False,
                detector='Falcon',
                detectorMode='Linear',
                pixelSize=1.1,
                dosePerFrame=1.0,
                totalDose=35.0,
                exposureTime=1.2,
                numOfFrames=48,
                numOfMovies=movies,
                numOfMics=mics,
                numOfCtfs=ctfs,
                numOfPtcls=ptcls,
                numOfCls2D=0,
                ptclSizeMin=140,
                ptclSizeMax=160,
            )
            self._db_session.add(new_session)
        self._db_session.commit()

        self.create_session(sessionData='dfhgrth',
                            userid=2,
                            sessionName='dfgerhsrth_NAME',
                            dateStarted=dt.datetime.now(),
                            description='Long description goes here.....',
                            status='Running',
                            microscope='KriosX',
                            voltage=300,
                            cs=2.7,
                            phasePlate=False,
                            detector='Falcon',
                            detectorMode='Linear',
                            pixelSize=1.1,
                            dosePerFrame=1.0,
                            totalDose=35.0,
                            exposureTime=1.2,
                            numOfFrames=48,
                            numOfMovies=0,
                            numOfMics=0,
                            numOfCtfs=0,
                            numOfPtcls=0,
                            numOfCls2D=0,
                            ptclSizeMin=140,
                            ptclSizeMax=160, )


