import unittest
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import os

import game


class ShrimpMechanicTests(unittest.TestCase):
    def test_level_mode_has_easier_opening_and_boss_every_ten_levels(self):
        game_obj = game.Game.__new__(game.Game)
        game_obj.game_mode = 'levels'
        game_obj.campaign_level = 1
        game_obj.wave = 1
        self.assertEqual(game_obj._wave_target_for_current_mode(), 5)

        game_obj.campaign_level = 10
        game_obj.wave = 5
        self.assertIs(game_obj._boss_class_for_wave(), game.SharkBoss)
        game_obj.campaign_level = 20
        game_obj.wave = 5
        self.assertIs(game_obj._boss_class_for_wave(), game.OctopusBoss)
        game_obj.campaign_level = 30
        game_obj.wave = 5
        self.assertIs(game_obj._boss_class_for_wave(), game.SharkBoss)

    def test_free_mode_keeps_its_original_boss_waves(self):
        game_obj = game.Game.__new__(game.Game)
        game_obj.game_mode = 'free'
        game_obj.wave = 10
        self.assertIs(game_obj._boss_class_for_wave(), game.SharkBoss)
        game_obj.wave = 25
        self.assertIs(game_obj._boss_class_for_wave(), game.OctopusBoss)
        game_obj.wave = 20
        self.assertIsNone(game_obj._boss_class_for_wave())

    def test_stamina_last_longer(self):
        self.assertEqual(game.STAMINA_DRAIN_SECONDS, 45)
        self.assertEqual(game.BOSS_STAMINA_DRAIN_SECONDS, 90)

    def test_completing_a_level_unlocks_the_next_one(self):
        game_obj = game.Game.__new__(game.Game)
        game_obj.game_mode = 'levels'
        game_obj.campaign_level = 1
        game_obj.unlocked_level = 1
        game_obj.completed_level = 0
        game_obj.wave = 5
        game_obj.wave_clear_timer = 0
        game_obj.boss = None
        game_obj.stamina = 50
        game_obj.max_stamina = 100
        game_obj.state = game.GameState.FLYING
        messages = []
        game_obj._add_message = messages.append
        game_obj._save_level_progress = lambda: None

        game_obj._next_wave()

        self.assertEqual(game_obj.completed_level, 1)
        self.assertEqual(game_obj.unlocked_level, 2)
        self.assertEqual(game_obj.state, game.GameState.LEVEL_COMPLETE)
        self.assertIn("Nivel 1 completado", messages[0])

    def test_campaign_progress_is_saved_and_loaded(self):
        with TemporaryDirectory() as temp_dir:
            progress_path = os.path.join(temp_dir, 'progress.json')
            game_obj = game.Game.__new__(game.Game)
            game_obj._level_progress_path = progress_path
            game_obj.unlocked_level = 3
            game_obj.completed_level = 2
            game_obj._save_level_progress()

            loaded_game = game.Game.__new__(game.Game)
            loaded_game._level_progress_path = progress_path
            loaded_game.unlocked_level = 1
            loaded_game.completed_level = 0
            loaded_game._load_level_progress()

            self.assertEqual(loaded_game.unlocked_level, 3)
            self.assertEqual(loaded_game.completed_level, 2)

    def test_ai_companion_keeps_flying_during_a_dive(self):
        for active_type in ('pelican', 'osprey'):
            moves = []
            pelican = type('BirdStub', (), {
                'hp': 20, 'state': 'flying', 'x': 260.0, 'y': 260.0,
                'frame': 0, 'move': lambda self, dx, dy: moves.append((dx, dy)),
            })()
            osprey = type('BirdStub', (), {
                'hp': 12, 'state': 'flying', 'x': 720.0, 'y': 190.0,
                'frame': 0, 'move': lambda self, dx, dy: moves.append((dx, dy)),
            })()
            game_obj = game.Game.__new__(game.Game)
            game_obj.pelican = pelican
            game_obj.osprey = osprey
            game_obj.active_bird = pelican if active_type == 'pelican' else osprey
            game_obj.state = game.GameState.UNDERWATER
            game_obj.puffer_list = []

            game_obj._update_ai_companion()

            self.assertTrue(moves)
            self.assertNotEqual(moves[0], (0, 0))

    def test_birds_reach_their_intended_dive_depths(self):
        playable_depth = game.SCREEN_HEIGHT - game.WATER_Y - 78

        self.assertEqual(game.Bird.CONFIGS['pelican']['dive_speed'], 11)
        self.assertEqual(game.Bird.CONFIGS['osprey']['dive_speed'], 15)
        self.assertEqual(game.Bird.CONFIGS['pelican']['max_depth'], playable_depth)
        self.assertEqual(game.Bird.CONFIGS['osprey']['max_depth'], playable_depth // 2)
        for config in game.Bird.CONFIGS.values():
            stopping_distance = 0
            vertical_speed = config['uw_entry_vy']
            while vertical_speed >= 0.25:
                stopping_distance += vertical_speed
                vertical_speed *= config['uw_decay']
            self.assertGreater(stopping_distance, config['max_depth'])

    def test_shrimp_pickup_spawns_when_requested(self):
        game_obj = game.Game.__new__(game.Game)
        game_obj.shrimp_pickups = []

        with patch('game.random.random', return_value=0.01):
            spawned = game_obj._maybe_spawn_shrimp_pickup(120, 180)

        self.assertTrue(spawned)
        self.assertEqual(len(game_obj.shrimp_pickups), 1)
        self.assertEqual(game_obj.shrimp_pickups[0].x, 120)
        self.assertEqual(game_obj.shrimp_pickups[0].y, 180)

    def test_shrimp_pickup_rewards_both_birds_underwater(self):
        for bird_type in ('pelican', 'osprey'):
            game_obj = game.Game.__new__(game.Game)
            game_obj.pelican = SimpleNamespace(
                hp=20, state='flying', x=700, y=100, capture_radius=48,
                bird_type='pelican')
            game_obj.osprey = SimpleNamespace(
                hp=12, state='flying', x=800, y=100, capture_radius=32,
                bird_type='osprey')
            bird = game_obj.pelican if bird_type == 'pelican' else game_obj.osprey
            bird.state = 'underwater'
            bird.x = bird.y = 200
            game_obj.shrimp_pickups = [game.ShrimpPickup(200, 200)]
            game_obj.shrimp_charge = 0
            game_obj.stamina = 50
            game_obj.max_stamina = 100
            game_obj._add_message = lambda message: None

            game_obj._collect_shrimp_pickups()

            self.assertEqual(game_obj.shrimp_pickups, [])
            if bird_type == 'pelican':
                self.assertEqual(game_obj.shrimp_charge, 1)
            else:
                self.assertEqual(game_obj.stamina, 65)

    def test_recovery_upgrade_increases_stamina_capacity(self):
        game_obj = game.Game.__new__(game.Game)
        game_obj.upgrades = {'depth': 0, 'capacity': 0, 'luck': 0, 'damage': 0, 'recovery': 2}
        game_obj.pelican = type('P', (), {'max_depth': 270, 'capture_radius': 48})()
        game_obj.osprey = type('O', (), {'max_depth': 140, 'capture_radius': 32})()
        game_obj.max_stamina = 100.0
        game_obj.stamina = 100.0
        game_obj._apply_upgrades()

        self.assertGreaterEqual(game_obj.max_stamina, 100.0)
        self.assertEqual(game_obj.upgrades['recovery'], 2)

    def test_combo_multiplier_increases_with_streak(self):
        game_obj = game.Game.__new__(game.Game)
        game_obj.combo = 4
        game_obj.combo_timer = 180
        self.assertEqual(game_obj._get_combo_multiplier(), 2)

        game_obj.combo = 10
        self.assertEqual(game_obj._get_combo_multiplier(), 3)

    def test_boss_reward_scales_with_combo(self):
        game_obj = game.Game.__new__(game.Game)
        game_obj.combo = 4
        self.assertEqual(game_obj._get_bonus_reward(25), 50)

    def test_game_main_entrypoint_exists_and_runs(self):
        with patch.object(game, 'Game', autospec=True) as mock_game_cls:
            mock_game = mock_game_cls.return_value
            game.main()

        mock_game_cls.assert_called_once_with()
        mock_game.run.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
