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


from sqlalchemy import (Column, Integer, String, JSON, Boolean, Float,
                        ForeignKey, Text)
from sqlalchemy.orm import relationship
from sqlalchemy_utc import UtcDateTime, utcnow
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


def create_data_models(dm, Base):
    """ Define the Data Models that will be use by the Data Manager. """

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

        # Booking authorization, who can book within this slot
        booking_auth = Column(JSON, default={'projects': [], 'users': []})

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

        created = Column(UtcDateTime,
                         index=False,
                         unique=False,
                         nullable=False,
                         default=utcnow())

        pi_id = Column(Integer, ForeignKey('users.id'),
                       nullable=True)
        pi = relationship("User", foreign_keys=[pi_id],
                          back_populates="lab_members")

        lab_members = relationship("User")

        # Default role should be: 'user'
        # more roles can be comma separated: 'user,admin,manager'
        roles = Column(String(128),
                       nullable=False,
                       default='user')

        password_hash = Column(String(256),
                               unique=True,
                               nullable=False)

        # one user to many sessions, bidirectional
        sessions = relationship('Session', back_populates="users")

        @staticmethod
        def create_password_hash(password):
            return generate_password_hash(password, method='sha256')

        def set_password(self, password):
            """Create hashed password."""
            self.password_hash = self.create_password_hash(password)

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

        def same_pi(self, other):
            """ Return if the same pi. """
            pi_id = self.id if self.is_pi else self.pi_id
            return pi_id == other.pi_id

        def get_projects(self):
            """ Return the projects that this users is involved,
            via its PI.
            """
            return self.projects if self.is_pi else self.pi[0].projects

    class Booking(Base):
        """Model for user accounts."""
        __tablename__ = 'bookings'

        id = Column(Integer,
                    primary_key=True)

        title = Column(String(256),
                       nullable=False)

        start = Column(UtcDateTime,
                       nullable=False)

        end = Column(UtcDateTime,
                     nullable=False)

        # booking, slot or downtime
        type = Column(String(16),
                      nullable=False)

        # slot authorization, who can book within this slot
        slot_auth = Column(JSON, default={'projects': [], 'users': []})

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

        repeat_id = Column(String(256), nullable=True)

        repeat_value = Column(String(32), nullable=False, default='no')

        def __repr__(self):
            return '<Booking {}>'.format(self.title)

        def json(self):
            return _json(self)

    class Project(Base):
        """
        Project that applies for access to the facility.
        Usually many principal investigators are associated to a project.
        """
        __tablename__ = 'projects'

        id = Column(Integer,
                    primary_key=True)

        code = Column(String(32),
                      nullable=False,
                      unique=True)

        alias = Column(String(32))

        title = Column(String(256),
                       nullable=False)

        description = Column(Text,
                             nullable=True)

        invoice_reference = Column(String(256),
                                   nullable=False)

        invoice_address = Column(Text,
                                 nullable=True)

        pi_id = Column(Integer, ForeignKey('users.id'),
                       nullable=False)
        pi = relationship("User", foreign_keys=[pi_id], backref="projects")

        def __repr__(self):
            return '<Project code=%s, alias=%s>' % (self.code, self.alias)

        def json(self):
            return _json(self)

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
        dateStarted = Column(UtcDateTime,
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

    dm.User = User
    dm.Resource = Resource
    dm.Booking = Booking
    dm.Session = Session
    dm.Project = Project

