import json
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8797"


def select(query, **settings):
    req = Request(BASE + "/api/select", data=json.dumps(dict(query=query, **settings)).encode(),
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=20) as r:
        return json.load(r)


class FieldTests(unittest.TestCase):
    def test_sound_paraphrase(self):
        result = select("I would like to hear the rustling and chirping around me", minutes=5,
                        movement="still", place="park")
        self.assertEqual(result["matches"][0]["id"], "sound-map")

    def test_social_walk(self):
        result = select("I'd love some fresh air and conversation with a companion", minutes=20,
                        movement="walk", place="urban")
        self.assertEqual(result["matches"][0]["id"], "friend-stroll")

    def test_budget_and_access(self):
        for minutes in (5, 10, 20, 30):
            for place in ("park", "urban", "balcony"):
                result = select("I want to quietly watch something outside", minutes=minutes,
                                movement="still", place=place)
                self.assertTrue(result["matches"])
                for c in result["matches"]:
                    self.assertLessEqual(c["minutes"], minutes)
                    self.assertEqual(c["movement"], "still")
                    self.assertIn(place, c["places"])

    def test_no_feasible_card(self):
        result = select("Go for a walk", minutes=5, movement="walk", place="balcony")
        self.assertEqual(result["matches"], [])

    def test_unrelated(self):
        self.assertEqual(select("Explain the SQL transaction isolation level")['matches'], [])

    def test_invalid_input(self):
        for query, settings in [("", {}), ("x" * 601, {}), ("birds", {"minutes": -1}),
                                ("birds", {"movement": "run"}), ("birds", {"place": "mars"})]:
            with self.assertRaises(HTTPError) as ctx:
                select(query, **settings)
            self.assertEqual(ctx.exception.code, 400)

    def test_unexpected_host_rejected(self):
        request = Request(BASE + "/api/select", data=json.dumps(dict(query="birds")).encode(),
            headers={"Content-Type": "application/json", "Host": "example.invalid:8797"})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 403)

    def test_cross_origin_rejected(self):
        req = Request(BASE + "/api/select", data=b'{"query":"birds"}',
                      headers={"Content-Type":"application/json", "Origin":"https://example.com"})
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req)
        self.assertEqual(ctx.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
