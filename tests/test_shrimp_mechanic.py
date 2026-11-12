import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os

import game


class ShrimpMechanicTests(unittest.TestCase):
    def test_pelican_burst_never_spends_more_ammo_than_available(self):
        game_obj = game.Game.__new__(game.Game)
        bird = game.Bird.__new__(game.Bird)
        bird.bird_type = 'pelican'
        bird.ammo = 4
        bird.special_cooldown = 0
        bird.x = bird.y = 100.0
        bird.burst_queue = 0
        bird.burst_interval = 0
        bird.facing_right = True
        bird.beak_open = 0
        game_obj.pelican = bird
        game_obj.state = game.GameState.FLYING
        game_obj.shrimp_charge = 0
        game_obj.bullets = []
        game_obj._add_message = lambda message: None
        game_obj._bullet_color = lambda active_bird: (255, 255, 255)

        with patch('game.pygame.mouse.get_pos', return_value=(200, 100)):
            game_obj._pelican_burst()
        for _ in range(8):
            bird.burst_interval = 0
            game_obj._tick_pelican_burst()

        self.assertEqual(len(game_obj.bullets), 4)
        self.assertEqual(bird.ammo, 0)
        self.assertEqual(bird.burst_queue, 0)

    def test_shrimp_charge_adds_six_special_burst_shots(self):
        game_obj = game.Game.__new__(game.Game)
        bird = game.Bird.__new__(game.Bird)
        bird.bird_type = 'pelican'
        bird.ammo = 8
        bird.special_cooldown = 0
        bird.x = bird.y = 100.0
        bird.burst_queue = 0
        bird.burst_interval = 0
        bird.facing_right = True
        bird.beak_open = 0
        game_obj.pelican = bird
        game_obj.state = game.GameState.FLYING
        game_obj.shrimp_charge = 1
        game_obj.bullets = []
        game_obj._add_message = lambda message: None
        game_obj._bullet_color = lambda active_bird: (255, 255, 255)

        with patch('game.pygame.mouse.get_pos', return_value=(200, 100)):
            game_obj._pelican_burst()
        for _ in range(8):
            bird.burst_interval = 0
            game_obj._tick_pelican_burst()

        shrimp_bullets = [bullet for bullet in game_obj.bullets
                          if isinstance(bullet, game.ShrimpBullet)]
        self.assertEqual(len(game_obj.bullets), 8)
        self.assertEqual(len(shrimp_bullets), 6)
        self.assertEqual(game_obj.shrimp_charge, 0)
        self.assertEqual(bird.ammo, 0)

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

    def test_progress_autosaves_every_five_seconds(self):
        game_obj = game.Game.__new__(game.Game)
        saved = []
        game_obj._progress_save_timer = 1
        game_obj._save_level_progress = lambda: saved.append(True)

        game_obj._tick_progress_autosave()

        self.assertEqual(saved, [True])
        self.assertEqual(game_obj._progress_save_timer, game.FPS * 5)

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
            game_obj.pelican_skins = [None] * 9
            game_obj.osprey_skins = [None] * 9
            game_obj.unlocked_pelican = {0, 4, 8}
            game_obj.unlocked_osprey = {0, 5}
            game_obj.pelican_skin_idx = 8
            game_obj.osprey_skin_idx = 5
            game_obj.caught_count = 480
            game_obj.upgrades = {'depth': 2, 'capacity': 1, 'luck': 0,
                                 'damage': 1, 'recovery': 2}
            game_obj.max_upgrade = 5
            game_obj.rebirth_count = 2
            game_obj.crabs_caught_total = 5
            game_obj.golden_caught_total = 10
            game_obj.normal_fish_caught = 12
            game_obj._save_level_progress()

            loaded_game = game.Game.__new__(game.Game)
            loaded_game._level_progress_path = progress_path
            loaded_game.unlocked_level = 1
            loaded_game.completed_level = 0
            loaded_game.pelican_skins = [None] * 9
            loaded_game.osprey_skins = [None] * 9
            loaded_game.unlocked_pelican = {0}
            loaded_game.unlocked_osprey = {0}
            loaded_game.pelican_skin_idx = 0
            loaded_game.osprey_skin_idx = 0
            loaded_game.caught_count = 0
            loaded_game.upgrades = {'depth': 0, 'capacity': 0, 'luck': 0,
                                    'damage': 0, 'recovery': 0}
            loaded_game.max_upgrade = 3
            loaded_game.rebirth_count = 0
            loaded_game.crabs_caught_total = 0
            loaded_game.golden_caught_total = 0
            loaded_game.normal_fish_caught = 0
            loaded_game._load_level_progress()

            self.assertEqual(loaded_game.unlocked_level, 3)
            self.assertEqual(loaded_game.completed_level, 2)
            self.assertEqual(loaded_game.unlocked_pelican, {0, 4, 8})
            self.assertEqual(loaded_game.unlocked_osprey, {0, 5})
            self.assertEqual(loaded_game.pelican_skin_idx, 8)
            self.assertEqual(loaded_game.osprey_skin_idx, 5)
            self.assertEqual(loaded_game.caught_count, 480)
            self.assertEqual(loaded_game.upgrades, game_obj.upgrades)
            self.assertEqual(loaded_game.max_upgrade, 5)
            self.assertEqual(loaded_game.rebirth_count, 2)
            self.assertEqual(loaded_game.crabs_caught_total, 5)
            self.assertEqual(loaded_game.golden_caught_total, 10)
            self.assertEqual(loaded_game.normal_fish_caught, 12)

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

        with patch('game.random.random', return_value=0.10):
            spawned = game_obj._maybe_spawn_shrimp_pickup(120, 180)

        self.assertTrue(spawned)
        self.assertEqual(len(game_obj.shrimp_pickups), 1)
        self.assertEqual(game_obj.shrimp_pickups[0].x, 120)
        self.assertEqual(game_obj.shrimp_pickups[0].y, 180)

    def test_shrimp_pickup_rewards_both_birds(self):
        game_obj = game.Game.__new__(game.Game)
        game_obj.shrimp_charge = 0
        game_obj.stamina = 20
        game_obj.max_stamina = 100
        game_obj._add_message = lambda message: None
        pickup = game.ShrimpPickup(120, 180)

        pelican = type('BirdStub', (), {'bird_type': 'pelican'})()
        game_obj._collect_shrimp_pickup(pelican, pickup)
        self.assertEqual(game_obj.shrimp_charge, 1)
        self.assertFalse(pickup.alive)

        osprey = type('BirdStub', (), {
            'bird_type': 'osprey', 'hp': 8, 'max_hp': 12,
        })()
        second_pickup = game.ShrimpPickup(120, 180)
        game_obj._collect_shrimp_pickup(osprey, second_pickup)
        self.assertEqual(osprey.hp, 9)
        self.assertEqual(game_obj.stamina, 32)
        self.assertFalse(second_pickup.alive)

    def test_shrimp_pickup_floats_up_to_the_surface(self):
        pickup = game.ShrimpPickup(120, game.SCREEN_HEIGHT - 55)

        frames_to_surface = int(pickup.y - pickup.float_y) + 100
        for _ in range(frames_to_surface):
            pickup.update()

        self.assertLess(pickup.y, game.WATER_Y)
        self.assertGreaterEqual(pickup.y, game.WATER_Y - 45)

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
