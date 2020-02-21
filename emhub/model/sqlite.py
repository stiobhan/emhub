from .. import db


class User(db.Model):
    """Model for user accounts."""
    __tablename__ = 'users'
    id = db.Column(db.Integer,
                   primary_key=True)
    username = db.Column(db.String(64),
                         index=True,
                         unique=True,
                         nullable=False)
    email = db.Column(db.String(80),
                      index=False,
                      unique=True,
                      nullable=False)
    created = db.Column(db.DateTime,
                        index=False,
                        unique=False,
                        nullable=False)
    admin = db.Column(db.Boolean,
                      index=False,
                      unique=False,
                      nullable=False)

    # one user to many sessions, bidirectional
    sessions = db.relationship('Session', back_populates="users")

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Session(db.Model):
    """Model for sessions."""
    __tablename__ = 'sessions'
    id = db.Column(db.Integer,
                   primary_key=True)
    sessionName = db.Column(db.String(80),
                            index=True,
                            unique=False,
                            nullable=False)
    dateStarted = db.Column(db.DateTime,
                            index=False,
                            unique=False,
                            nullable=False)
    description = db.Column(db.Text,
                            index=False,
                            unique=False,
                            nullable=True)
    status = db.Column(db.String(20),
                       index=False,
                       unique=False,
                       nullable=False)
    microscope = db.Column(db.String(64),
                           index=False,
                           unique=False,
                           nullable=False)
    voltage = db.Column(db.Integer,
                        index=False,
                        unique=False,
                        nullable=False)
    cs = db.Column(db.Float,
                   index=False,
                   unique=False,
                   nullable=False)
    phasePlate = db.Column(db.Boolean,
                           index=False,
                           unique=False,
                           nullable=False)
    detector = db.Column(db.String(64),
                         index=False,
                         unique=False,
                         nullable=False)
    detectorMode = db.Column(db.String(64),
                             index=False,
                             unique=False,
                             nullable=False)
    pixelSize = db.Column(db.Float,
                          index=False,
                          unique=False,
                          nullable=False)
    dosePerFrame = db.Column(db.Float,
                             index=False,
                             unique=False,
                             nullable=False)
    totalDose = db.Column(db.Float,
                          index=False,
                          unique=False,
                          nullable=False)
    exposureTime = db.Column(db.Float,
                             index=False,
                             unique=False,
                             nullable=False)
    numOfFrames = db.Column(db.Integer,
                            index=False,
                            unique=False,
                            nullable=False)
    numOfMovies = db.Column(db.Integer,
                            index=False,
                            unique=False,
                            nullable=False)
    numOfMics = db.Column(db.Integer,
                          index=False,
                          unique=False,
                          nullable=False)
    numOfCtfs = db.Column(db.Integer,
                          index=False,
                          unique=False,
                          nullable=False)
    numOfPtcls = db.Column(db.Integer,
                           index=False,
                           unique=False,
                           nullable=False)
    numOfCls2D = db.Column(db.Integer,
                           index=False,
                           unique=False,
                           nullable=False)
    ptclSizeMin = db.Column(db.Integer,
                            index=False,
                            unique=False,
                            nullable=False)
    ptclSizeMax = db.Column(db.Integer,
                            index=False,
                            unique=False,
                            nullable=False)

    # one user to many sessions, bidirectional
    userid = db.Column(db.Integer, db.ForeignKey('users.id'),
                       nullable=False)
    users = db.relationship("User", back_populates="sessions")

    def __repr__(self):
        return '<Session {}>'.format(self.sessionName)
