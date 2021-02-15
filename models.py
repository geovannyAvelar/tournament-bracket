from config import db, ma
from enum import Enum
from marshmallow_enum import EnumField

class Competitor(db.Model):
    __tablename__ = 'competitor'

    competitor_id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.tournament_id'))

    def __init__(self, name):
        self.name = name

    def __repr__(self) -> str:
        return self.name

class CompetitorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Competitor
        include_relationships = True
        load_instance = True

class Result(Enum):
    HOME_VICTORY = "HOME_VICTORY"
    GUEST_VICTORY = "GUEST_VICTORY"

class Match(db.Model):
    __tablename__ = 'match'

    match_id = db.Column(db.Integer, primary_key = True)

    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.tournament_id'))

    home_id = db.Column(db.Integer, db.ForeignKey('competitor.competitor_id'))
    home = db.relationship("Competitor", foreign_keys = [home_id])

    guest_id = db.Column(db.Integer, db.ForeignKey('competitor.competitor_id'))
    guest = db.relationship("Competitor", foreign_keys = [guest_id])

    match_number = db.Column(db.Integer)
    fixture_number = db.Column(db.Integer)

    result = db.Column(db.Enum(Result))

    def get_winner(self) -> Competitor:
        if self.result is None:
            return None

        if self.result == Result.HOME_VICTORY:
            return self.home
        else:
            return self.guest

    def get_loser(self) -> Competitor:
        if self.result is None:
            return None

        if self.result == Result.HOME_VICTORY:
            return self.guest
        else:
            return self.home

    def __str__(self) -> str:
        return self.home.name + " X " + self.guest.name

class MatchSchema(ma.SQLAlchemyAutoSchema):
    result = EnumField(Result, by_value = True)

    class Meta:
        model = Match
        include_relationships = True
        load_instance = True

class Tournament(db.Model):
    __tablename__ = 'tournament'

    tournament_id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String)

    competitors = db.relationship(
        'Competitor',
        backref = 'tournament',
        cascade = "all, delete, delete-orphan",
        single_parent = True
    )

    matches = db.relationship(
        'Match',
        backref = 'tournament',
        cascade = "all, delete, delete-orphan",
        single_parent = True
    )

    def __init__(self, name):
        self.name = name

    def add_competitor(self, competitor):
        self.competitors.append(competitor)

    def __repr__(self) -> str:
        return "<Tournament(id=%s, name='%s')>" %(self.id, self.name)

class TournamentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Tournament
        include_relationships = True
        load_instance = True