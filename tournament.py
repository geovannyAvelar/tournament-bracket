from models import Tournament, TournamentSchema
from models import CompetitorSchema
from models import Match, MatchSchema, Result
from config import db

from sqlalchemy import and_

from flask import abort

from random import randint
import math

def read_all():
    tournaments = Tournament.query.all()
    tournament_schema = TournamentSchema(many = True)
    return tournament_schema.dump(tournaments)

def read_one(tournament_id):
    tournament = Tournament.query.filter(Tournament.tournament_id == tournament_id).one_or_none()

    if tournament is not None:
        tournament_schema = TournamentSchema()
        data = tournament_schema.dump(tournament)
        return data
    else:
        abort(404, "Tournament not found")

def create(tournament):
    schema = TournamentSchema()
    new_tournament = schema.load(tournament, session = db.session)

    db.session.add(new_tournament)
    db.session.commit()

    data = schema.dump(new_tournament)

    return data, 201

def create_competitor(tournament_id, competitor):
    tournament = Tournament.query.filter(Tournament.tournament_id == tournament_id).one_or_none()

    if tournament is not None:
        schema = CompetitorSchema()
        new_competitor = schema.load(competitor, session = db.session)
        new_competitor.tournament_id = tournament_id

        db.session.add(new_competitor)
        db.session.commit()

        data = schema.dump(new_competitor)

        return data, 201
    else:
        abort(404, "Tournament not found")

def read_matches(tournament_id):
    tournament = Tournament.query.filter(Tournament.tournament_id == tournament_id).one_or_none()

    if tournament is not None:
        schema = MatchSchema(many = True)
        return schema.dump(tournament.matches)
    else:
        abort(404, "Tournament not found")

def set_match_result(tournament_id, match_id, result):
    if result['name'] != "HOME_VICTORY" and result['name'] != "GUEST_VICTORY":
        abort(400, "Invalid result. Inform a type of result (HOME_VICTORY or GUEST_VICTORY)")

    match = Match.query.filter(and_(Match.match_id == match_id,
                                    Match.tournament_id == tournament_id)).one_or_none()

    if match is not None:
        match.result = Result[result['name']]
        db.session.merge(match)
        db.session.commit()

        return 201
    else:
        abort(404, "Match not found")

def draw_first_fixture(tournament_id):
    tournament = Tournament.query.filter(Tournament.tournament_id == tournament_id).one_or_none()

    Match.query.filter(Match.tournament_id == tournament_id).delete()

    if tournament is not None:
        competitors = tournament.competitors.copy()
        competitors_number = len(competitors)

        if competitors_number < 2 or competitors_number % 2 != 0:
            abort(400, "Insufficient number of competitors")

        match_number = 1

        for _ in competitors:
            random_home = randint(0, len(competitors) - 1)
            random_guest = randint(0, len(competitors) - 1)

            while random_home == random_guest:
                random_guest = randint(0, len(competitors) - 1)

            home = competitors[random_home]
            guest = competitors[random_guest]

            new_match = Match()
            new_match.fixture_number = 1
            new_match.match_number = match_number
            new_match.home = home
            new_match.home_id = home.competitor_id
            new_match.guest = guest
            new_match.guest_id = guest.competitor_id
            new_match.tournament_id = tournament.tournament_id

            match_number = match_number + 1

            competitors.remove(home)
            competitors.remove(guest)

            db.session.add(new_match)
            db.session.commit()

        return 201
    else:
        abort(404, "Tournament not found")

def calculate_results(tournament_id, fixture):
    matches = Match.query.filter(and_(Match.tournament_id == tournament_id, 
                                      Match.fixture_number == fixture)).all()

    if len(matches) % 2 == 0:
        Match.query.filter(and_(Match.tournament_id == tournament_id, 
                                Match.fixture_number == fixture + 1)).delete()

        pairs = [matches[i:i + 2] for i in range(0, len(matches), 2)]

        for i, pair in enumerate(pairs):
            first_match = pair[0]
            second_match = pair[1]

            if first_match.result == None or second_match.result == None:
                message = ("Cannot generate fixture results."
                            " Match ID {0} and Match ID {1} result should be defined first")
                abort(400, message.format(pair[0].match_id, pair[1].match_id))

            new_match = Match()
            new_match.tournament_id = tournament_id
            new_match.match_number = i + 1
            new_match.fixture_number = fixture + 1

            if first_match.result == Result.HOME_VICTORY:
                new_match.home = first_match.home
                new_match.home_id = first_match.home.competitor_id
            else:
                new_match.home = first_match.guest
                new_match.home_id = first_match.guest_id

            if second_match.result == Result.HOME_VICTORY:
                new_match.guest = second_match.home
                new_match.guest_id = second_match.home_id
            else:
                new_match.guest = second_match.guest
                new_match.guest_id = second_match.guest_id

            db.session.add(new_match)

        # Generating third place match
        if len(pair) == 1:
            first_match = pair[0]
            second_match = pair[1]

            new_match = Match()
            new_match.tournament_id = tournament_id
            new_match.match_number = 1
            new_match.fixture_number = -1

            new_match.home = first_match.get_loser()
            new_match.home_id = first_match.get_loser().competitor_id

            new_match.guest = second_match.get_loser()
            new_match.guest = second_match.get_loser().competitor_id

            db.session.add(new_match)

        db.session.commit()

        return 201

    abort(400, "Wrong number of matches")

def calculate_top_4(tournament_id):
    tournament = Tournament.query.filter(Tournament.tournament_id == tournament_id).one_or_none()

    if tournament is not None:
        competitors_number = len(tournament.competitors)
        fixtures_number = math.sqrt(competitors_number)

        final_match = Match.query.filter(and_(Match.tournament_id == tournament_id, 
                                             Match.fixture_number == fixtures_number)).one_or_none()
        third_place_match = Match.query.filter(and_(Match.tournament_id == tournament_id,
                                                    Match.fixture_number == -1)).all()

        if (final_match is not None and third_place_match is not None and 
            final_match.result is not None and third_place_match.result is not None):

            top_4 = [final_match.get_winner(), final_match.get_loser(), 
                     third_place_match.get_winner(), third_place_match.get_loser()]

            schema = MatchSchema(many = True)
            return schema.dump(top_4)
        else:
            abort(400, "Cannot calculate final results. Final and third place matches not defined")

    else:
        abort(404, "Tournament not found")