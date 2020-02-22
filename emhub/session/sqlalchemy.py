import os
from datetime import datetime as dt

from sqlalchemy import (create_engine, Column, Integer, String, DateTime,
                        Boolean, Float, ForeignKey, Text, text)
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base


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

        # FIXME: models are redefined every time app is launched
        self.__createModels(Base)

        # Create the database if it does not exists
        if not os.path.exists(sqlitePath):
            Base.metadata.create_all(bind=engine)
            # populate db with test data
            self.__populateTestData()

    def get_sessions(self, condition=None, orderBy=None):
        """ Returns a list.
        condition example: text("id<:value and name=:name")
        """
        if condition is not None and orderBy is None:
            return self.Session.query.filter(text(condition)).all()
        elif condition is not None and orderBy is not None:
            return self.Session.query.filter(text(condition)).order_by(orderBy).all()
        else:
            return self.Session.query.all()

    def create_session(self, sessionId, **attrs):
        """ Add a new session row. """
        new_session = self.Session(**attrs)
        self._db_session.add(new_session)
        self._db_session.commit()

    def update_session(self, sessionId, **attrs):
        """ Update session attrs. """
        session = self.Session.query.get(sessionId)

        for attr in attrs.items():
            session.attr = attrs[attr]

        self._db_session.commit()

    def delete_session(self, sessionId):
        """ Remove a session row. """
        session = self.Session.query.get(sessionId)
        self._db_session.delete(session)
        self._db_session.commit()

    def load_session(self, sessionId):
        return self.Session.query.get(sessionId)

    def close(self):
        self._db_session.remove()

    def __createModels(self, Base):
        class User(Base):
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
            created = Column(DateTime,
                             index=False,
                             unique=False,
                             nullable=False)
            admin = Column(Boolean,
                           index=False,
                           unique=False,
                           nullable=False)

            # one user to many sessions, bidirectional
            sessions = relationship('Session', back_populates="users")

            def __repr__(self):
                return '<User {}>'.format(self.username)

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

        self.User = User
        self.Session = Session

    def __populateTestData(self):
        # Create user table
        usernames = ['name1', 'name2', 'name3']
        emails = ['abc@def.com', 'fgh@ert.com', 'yu@dfh.com']

        for user, email in zip(usernames, emails):
            new_user = self.User(username=user,
                            email=email,
                            created=dt.now(),
                            admin=False)
            self._db_session.add(new_user)

        # Create sessions table.
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
                dateStarted=dt.now(),
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