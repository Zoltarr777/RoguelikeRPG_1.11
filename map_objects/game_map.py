import tcod as libtcod
from random import randint

import random

from components.ai import BasicMonster, MindControlled
from components.equipment import EquipmentSlots
from components.equippable import Equippable
from components.fighter import Fighter
from components.item import Item
from components.stairs import Stairs
from entity import Entity
from game_messages import Message
from item_functions import cast_confusion, cast_fireball, cast_lightning, heal, cast_sleep, cast_sleep_aura, health_talisman_sacrifice, cast_mind_control, necromancy
from map_objects.rectangle import Rect
from map_objects.tile import Tile

from random_utils import from_dungeon_level, random_choice_from_dict

from render_functions import RenderOrder


class GameMap:
	def __init__(self, width, height, dungeon_level=1):
		self.width = width
		self.height = height
		self.tiles = self.initialize_tiles()

		self.dungeon_level = dungeon_level

	def initialize_tiles(self):
		tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]

		return tiles

	def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities):
		rooms = []
		num_rooms = 0

		center_of_last_room_x = None
		center_of_last_room_y = None

		for r in range(max_rooms):
			w = randint(room_min_size, room_max_size)
			h = randint(room_min_size, room_max_size)

			x = randint(0, map_width - w - 1)
			y = randint(0, map_height - h - 1)

			new_room = Rect(x, y, w, h)

			for other_room in rooms:
				if new_room.intersect(other_room):
					break
			else:
				self.create_room(new_room)

				(new_x, new_y) = new_room.center()

				center_of_last_room_x = new_x
				center_of_last_room_y = new_y

				if num_rooms == 0:
					player.x = new_x
					player.y = new_y
				else:
					(prev_x, prev_y) = rooms[num_rooms - 1].center()

					if randint(0, 1) == 1:
						self.create_h_tunnel(prev_x, new_x, prev_y)
						self.create_v_tunnel(prev_y, new_y, new_x)
					else:
						self.create_v_tunnel(prev_y, new_y, prev_x)
						self.create_h_tunnel(prev_x, new_x, new_y)

				self.place_entities(new_room, entities)


				rooms.append(new_room)
				num_rooms += 1

		stairs_component = Stairs(self.dungeon_level + 1)
		down_stairs = Entity(center_of_last_room_x, center_of_last_room_y, '>', libtcod.white, 'Stairs', render_order=RenderOrder.STAIRS, stairs=stairs_component)
		entities.append(down_stairs)

	def create_room(self, room):
		for x in range(room.x1 + 1, room.x2):
			for y in range(room.y1 + 1, room.y2):
				self.tiles[x][y].blocked = False
				self.tiles[x][y].block_sight = False

	def create_h_tunnel(self, x1, x2, y):
		for x in range(min(x1, x2), max(x1, x2) + 1):
			self.tiles[x][y].blocked = False
			self.tiles[x][y].block_sight = False

	def create_v_tunnel(self, y1, y2, x):
		for y in range(min(y1, y2), max(y1, y2) + 1):
			self.tiles[x][y].blocked = False
			self.tiles[x][y].block_sight = False

	def place_entities(self, room, entities):
		max_monsters_per_room = from_dungeon_level([[2, 1], [4, 4], [6, 6], [8, 10]], self.dungeon_level)
		max_items_per_room = from_dungeon_level([[1, 1], [2, 8]], self.dungeon_level)
		number_of_monsters = randint(0, max_monsters_per_room)
		number_of_items = randint(0, max_items_per_room)

		monster_chances = {
			'goblin': from_dungeon_level([[80, 1], [60, 3], [30, 5], [0, 7]], self.dungeon_level),
			'orc': from_dungeon_level([[40, 2], [50, 3], [20, 10]], self.dungeon_level),
			'troll': from_dungeon_level([[20, 3], [40, 5], [60, 7]], self.dungeon_level),
			'basilisk': from_dungeon_level([[20, 7], [30, 9], [40, 11]], self.dungeon_level),
			'ghost': from_dungeon_level([[40, 5]], self.dungeon_level)
		}

		item_descriptors = [
			'Valor', 'Power', 'Ingenuity', 'Glory', 'Strength', 'Speed', 
			'Wealth', 'Divinity', 'Energy', 'Honor', 'Resistance', 'Greatness'
		]

		item_chances = {
			'healing_potion': from_dungeon_level([[15, 1], [10, 8]], self.dungeon_level),
			'greater_healing_potion': from_dungeon_level([[30, 8]], self.dungeon_level),
			'terrium_sword': from_dungeon_level([[15, 3], [0, 10]], self.dungeon_level),
			'terrium_shield': from_dungeon_level([[15, 3], [0, 10]], self.dungeon_level),
			'terrium_chestplate': from_dungeon_level([[15, 4], [0, 10]], self.dungeon_level),
			'terrium_leg_armor': from_dungeon_level([[15, 4], [0, 10]], self.dungeon_level),
			'terrium_helmet': from_dungeon_level([[20, 3], [0, 10]], self.dungeon_level),
			'terrium_amulet': from_dungeon_level([[10, 5], [0, 10]], self.dungeon_level),
			'ferrium_sword': from_dungeon_level([[15, 10], [0, 20]], self.dungeon_level),
			'ferrium_shield': from_dungeon_level([[15, 10], [0, 20]], self.dungeon_level),
			'ferrium_chestplate': from_dungeon_level([[15, 10], [0, 20]], self.dungeon_level),
			'ferrium_leg_armor': from_dungeon_level([[15, 10], [0, 20]], self.dungeon_level),
			'ferrium_helmet': from_dungeon_level([[20, 10], [0, 20]], self.dungeon_level),
			'ferrium_amulet': from_dungeon_level([[10, 10], [0, 20]], self.dungeon_level),
			'aurium_sword': from_dungeon_level([[15, 20]], self.dungeon_level),
			'aurium_shield': from_dungeon_level([[15, 20]], self.dungeon_level),
			'aurium_chestplate': from_dungeon_level([[15, 20]], self.dungeon_level),
			'aurium_leg_armor': from_dungeon_level([[15, 20]], self.dungeon_level),
			'aurium_helmet': from_dungeon_level([[20, 20]], self.dungeon_level),
			'aurium_amulet': from_dungeon_level([[10, 20]], self.dungeon_level),
			'lightning_spell': from_dungeon_level([[25, 3]], self.dungeon_level),
			'fireball_spell': from_dungeon_level([[25, 4]], self.dungeon_level),
			'confusion_spell': from_dungeon_level([[25, 2]], self.dungeon_level),
			'sleep_spell': from_dungeon_level([[25, 4]], self.dungeon_level),
			'sleep_aura': from_dungeon_level([[25, 5]], self.dungeon_level),
			'health_talisman': from_dungeon_level([[20, 10]], self.dungeon_level),
			'wizard_staff': from_dungeon_level([[25, 10]], self.dungeon_level),
			'mind_control_spell': from_dungeon_level([[25, 15]], self.dungeon_level),
			'necromancy_spell': from_dungeon_level([[20, 10]], self.dungeon_level)
		}

		for i in range(number_of_monsters):
			x = randint(room.x1 + 1, room.x2 - 1)
			y = randint(room.y1 + 1, room.y2 - 1)

			if not any([entity for entity in entities if entity.x == x and entity.y == y]):
				monster_choice = random_choice_from_dict(monster_chances)

				if monster_choice == 'goblin':
					fighter_component = Fighter(hp=4, defense=0, power=2, magic=0, magic_defense=0, xp=20, talismanhp=0, gold=randint(0, 2))
					ai_component = BasicMonster()
					monster = Entity(x, y, 'g', libtcod.darker_chartreuse, 'Goblin', blocks=True,
						render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
				elif monster_choice == 'orc':
					fighter_component = Fighter(hp=10, defense=0, power=3, magic=0, magic_defense=1, xp=40, talismanhp=0, gold=randint(1, 5))
					ai_component = BasicMonster()
					monster = Entity(x, y, 'o', libtcod.desaturated_green, 'Orc', blocks=True,
						render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
				elif monster_choice == 'troll':
					fighter_component = Fighter(hp=14, defense=2, power=5, magic=0, magic_defense=2, xp=100, talismanhp=0, gold=randint(3, 7))
					ai_component = BasicMonster()
					monster = Entity(x, y, 'T', libtcod.darker_green, 'Troll', blocks=True, fighter=fighter_component,
						render_order=RenderOrder.ACTOR, ai=ai_component)
				elif monster_choice == 'ghost':
					fighter_component = Fighter(hp=10, defense=0, power=0, magic=5, magic_defense=2, xp=50, talismanhp=0, gold=0)
					ai_component = BasicMonster()
					monster = Entity(x, y, 'G', libtcod.white, 'Ghost', blocks=True,
						render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
				else:
					fighter_component = Fighter(hp=20, defense=3, power=8, magic=0, magic_defense=3, xp=200, talismanhp=0, gold=randint(10, 20))
					ai_component = BasicMonster()
					monster = Entity(x, y, 'B', libtcod.darker_red, 'Basilisk', blocks=True, fighter=fighter_component,
						render_order=RenderOrder.ACTOR, ai=ai_component)

				entities.append(monster)

		for i in range(number_of_items):
			x = randint(room.x1 + 1, room.x2 - 1)
			y = randint(room.y1 + 1, room.y2 - 1)

			if not any([entity for entity in entities if entity.x == x and entity.y == y]):
				item_choice = random_choice_from_dict(item_chances)

				if item_choice == 'healing_potion':
					heal1_amount = 20
					item_component = Item(use_function=heal, amount=heal1_amount)
					item = Entity(x, y, '&', libtcod.violet, "Health Potion" + " (+" + str(heal1_amount) + " HP)", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'greater_healing_potion':
					heal2_amount = 40
					item_component = Item(use_function=heal, amount=heal2_amount)
					item = Entity(x, y, '&', libtcod.red, "Greater Healing Potion" + " (+" + str(heal2_amount) + " HP)", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'terrium_sword':
					sword_amount = randint(2, 4)
					equippable_component = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=sword_amount)
					item = Entity(x, y, '/', libtcod.darker_grey, "Terrium Sword of " + random.choice(item_descriptors) + " (+" + str(sword_amount) + " atk)", equippable=equippable_component)
				elif item_choice == 'terrium_shield':
					shield_amount = randint(1, 2)
					equippable_component = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=shield_amount)
					item = Entity(x, y, '[', libtcod.darker_grey, "Terrium Shield of " + random.choice(item_descriptors) + " (+" + str(shield_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'terrium_chestplate':
					chestplate_amount = randint(2, 3)
					equippable_component = Equippable(EquipmentSlots.CHEST, defense_bonus=chestplate_amount)
					item = Entity(x, y, 'M', libtcod.darker_grey, "Terrium Chestplate of " + random.choice(item_descriptors) + " (+" + str(chestplate_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'terrium_leg_armor':
					leg_amount = randint(1, 3)
					equippable_component = Equippable(EquipmentSlots.LEGS, defense_bonus=leg_amount)
					item = Entity(x, y, 'H', libtcod.darker_grey, "Terrium Leg Armor of " + random.choice(item_descriptors) + " (+" + str(leg_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'terrium_helmet':
					helmet_amount = randint(1, 2)
					equippable_component = Equippable(EquipmentSlots.HEAD, defense_bonus=helmet_amount)
					item = Entity(x, y, '^', libtcod.darker_grey, "Terrium Helmet of " + random.choice(item_descriptors) + " (+" + str(helmet_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'terrium_amulet':
					amulet_amount = randint(1, 4)
					equippable_component = Equippable(EquipmentSlots.AMULET, magic_bonus=amulet_amount)
					item = Entity(x, y, '*', libtcod.darker_grey, "Terrium Amulet of " + random.choice(item_descriptors) + " (+" + str(amulet_amount) + " mgk)", equippable=equippable_component)
				elif item_choice == 'ferrium_sword':
					sword_amount = randint(6, 10)
					equippable_component = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=sword_amount)
					item = Entity(x, y, '/', libtcod.darker_orange, "Ferrium Sword of " + random.choice(item_descriptors) + " (+" + str(sword_amount) + " atk)", equippable=equippable_component)
				elif item_choice == 'ferrium_shield':
					shield_amount = randint(4, 6)
					equippable_component = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=shield_amount)
					item = Entity(x, y, '[', libtcod.darker_orange, "Ferrium Shield of " + random.choice(item_descriptors) + " (+" + str(shield_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'ferrium_chestplate':
					chestplate_amount = randint(5, 7)
					equippable_component = Equippable(EquipmentSlots.CHEST, defense_bonus=chestplate_amount)
					item = Entity(x, y, 'M', libtcod.darker_orange, "Ferrium Chestplate of " + random.choice(item_descriptors) + " (+" + str(chestplate_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'ferrium_leg_armor':
					leg_amount = randint(4, 6)
					equippable_component = Equippable(EquipmentSlots.LEGS, defense_bonus=leg_amount)
					item = Entity(x, y, 'H', libtcod.darker_orange, "Ferrium Leg Armor of " + random.choice(item_descriptors) + " (+" + str(leg_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'ferrium_helmet':
					helmet_amount = randint(4, 5)
					equippable_component = Equippable(EquipmentSlots.HEAD, defense_bonus=helmet_amount)
					item = Entity(x, y, '^', libtcod.darker_orange, "Ferrium Helmet of " + random.choice(item_descriptors) + " (+" + str(helmet_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'ferrium_amulet':
					amulet_amount = randint(5, 9)
					equippable_component = Equippable(EquipmentSlots.AMULET, magic_bonus=amulet_amount)
					item = Entity(x, y, '*', libtcod.darker_orange, "Ferrium Amulet of " + random.choice(item_descriptors) + " (+" + str(amulet_amount) + " mgk)", equippable=equippable_component)
				elif item_choice == 'aurium_sword':
					sword_amount = randint(15, 20)
					equippable_component = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=sword_amount)
					item = Entity(x, y, '/', libtcod.crimson, "Aurium Sword of " + random.choice(item_descriptors) + " (+" + str(sword_amount) + " atk)", equippable=equippable_component)
				elif item_choice == 'aurium_shield':
					shield_amount = randint(8, 13)
					equippable_component = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=shield_amount)
					item = Entity(x, y, '[', libtcod.crimson, "Aurium Shield of " + random.choice(item_descriptors) + " (+" + str(shield_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'aurium_chestplate':
					chestplate_amount = randint(10, 15)
					equippable_component = Equippable(EquipmentSlots.CHEST, defense_bonus=chestplate_amount)
					item = Entity(x, y, 'M', libtcod.crimson, "Aurium Chestplate of " + random.choice(item_descriptors) + " (+" + str(chestplate_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'aurium_leg_armor':
					leg_amount = randint(8, 13)
					equippable_component = Equippable(EquipmentSlots.LEGS, defense_bonus=leg_amount)
					item = Entity(x, y, 'H', libtcod.crimson, "Aurium Leg Armor of " + random.choice(item_descriptors) + " (+" + str(leg_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'aurium_helmet':
					helmet_amount = randint(8, 12)
					equippable_component = Equippable(EquipmentSlots.HEAD, defense_bonus=helmet_amount)
					item = Entity(x, y, '^', libtcod.crimson, "Aurium Helmet of " + random.choice(item_descriptors) + " (+" + str(helmet_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'aurium_amulet':
					amulet_amount = randint(10, 15)
					equippable_component = Equippable(EquipmentSlots.AMULET, magic_bonus=amulet_amount)
					item = Entity(x, y, '*', libtcod.crimson, "Aurium Amulet of " + random.choice(item_descriptors) + " (+" + str(amulet_amount) + " mgk)", equippable=equippable_component)
				elif item_choice == 'fireball_spell':
					item_component = Item(use_function=cast_fireball, targeting=True, targeting_message=Message("Left click a target tile for the fireball, or right click to cancel.", libtcod.light_cyan), damage=15, radius=3)
					item = Entity(x, y, '#', libtcod.red, "Fireball Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'confusion_spell':
					item_component = Item(use_function=cast_confusion, targeting=True, targeting_message=Message("Left click an enemy to confuse it, or right click to cancel.", libtcod.light_cyan))
					item = Entity(x, y, '#', libtcod.light_pink, "Confusion Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'sleep_spell':
					item_component = Item(use_function=cast_sleep, targeting=True, targeting_message=Message("Left click an enemy to make it fall asleep, or right click to cancel.", libtcod.light_cyan))
					item = Entity(x, y, '#', libtcod.light_azure, "Sleep Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'sleep_aura':
					item_component = Item(use_function=cast_sleep_aura, targeting=True, targeting_message=Message("Left click a target tile to cast the sleep aura, or right click to cancel.", libtcod.light_cyan), radius=3)
					item = Entity(x, y, '#', libtcod.light_azure, "Sleep Aura Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'mind_control_spell':
					item_component = Item(use_function=cast_mind_control, targeting=True, targeting_message=Message("Left click a target tile to cast mind control, or right click to cancel.", libtcod.light_cyan), radius=3)
					item = Entity(x, y, '#', libtcod.purple, "Mind Control Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'health_talisman':
					item_component = Item(use_function=health_talisman_sacrifice, amount=5)
					item = Entity(x, y, '?', libtcod.darker_orange, "Health Talisman", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'wizard_staff':
					item_component = Item(use_function=cast_magic, damage=5, maximum_range=5)
					item = Entity(x, y, '|', libtcod.darker_sepia, "Wizard Staff", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'necromancy_spell':
					item_component = Item(use_function=necromancy, number_of_monsters=5)
					item = Entity(x, y, '#', libtcod.darker_red, "Necromancy Spell", render_order=RenderOrder.ITEM, item=item_component)
				else:
					item_component = Item(use_function=cast_lightning, damage=30, maximum_range=5)
					item = Entity(x, y, '#', libtcod.blue, "Lightning Spell", render_order=RenderOrder.ITEM, item=item_component)
				entities.append(item)


	def is_blocked(self, x, y):
		if self.tiles[x][y].blocked:
			return True

		return False

	def next_floor(self, player, message_log, constants):
		self.dungeon_level += 1
		entities = [player]

		self.tiles = self.initialize_tiles()
		self.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'], constants['map_width'], constants['map_height'], player, entities)

		player.fighter.heal(player.fighter.max_hp // 3)

		message_log.add_message(Message("You take a moment to rest, and recover your strength.", libtcod.light_violet))

		return entities