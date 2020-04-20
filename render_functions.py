import libtcodpy as libtcod

from enum import Enum

from game_states import GameStates

from menus import character_screen, inventory_menu, level_up_menu, bag_menu, help_menu, equipment_inventory_menu, quit_menu, drop_menu

from components.inventory import Inventory

class RenderOrder(Enum):
    STAIRS = 1
    CORPSE = 2
    ITEM = 3
    ACTOR = 4

def get_names_under_mouse(mouse, entities, fov_map):
    (x, y) = (mouse.cx, mouse.cy)

    names = [entity.name for entity in entities if entity.x == x and entity.y == y and libtcod.map_is_in_fov(fov_map, entity.x, entity.y)]

    names = ', '.join(names)

    return names.capitalize()

def render_bar(panel, x, y, total_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * total_width)

    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, int(x + total_width / 2), y, libtcod.BKGND_NONE, libtcod.CENTER, "{0}: {1}/{2}".format(name, value, maximum))


def render_all(con, panel, entities, player, game_map, fov_map, fov_recompute, message_log, screen_width, screen_height, bar_width, panel_height, panel_y, mouse, colors, game_state):
    if fov_recompute:
        for y in range(game_map.height):
            for x in range(game_map.width):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = game_map.tiles[x][y].block_sight

                if visible:
                    if wall:
                        libtcod.console_set_char_background(con, x, y, colors.get('light_wall'), libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, colors.get('light_ground'), libtcod.BKGND_SET)

                    game_map.tiles[x][y].explored = True
                elif game_map.tiles[x][y].explored:
                    if wall:
                        libtcod.console_set_char_background(con, x, y, colors.get('dark_wall'), libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, colors.get('dark_ground'), libtcod.BKGND_SET)

    entities_in_render_order = sorted(entities, key=lambda x: x.render_order.value)

    for entity in entities_in_render_order:
        draw_entity(con, entity, fov_map, game_map)

    libtcod.console_set_default_foreground(con, libtcod.white)
    libtcod.console_print_ex(con, 1, screen_height - 2, libtcod.BKGND_NONE, libtcod.LEFT, "HP: {0:02}/{1:02}".format(player.fighter.hp, player.fighter.max_hp))


    ''' Danny code to center player and have window scroll
    r = 20
    libtcod.console_blit(con, player.x - r, player.y - r, 2*r+1, 2*r+1, 0, int(screen_width/2) - r, int(screen_height/2) - r)
    '''
    libtcod.console_blit(con, 0, 0, screen_width, screen_height, 0, 0, 0)

    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)

    y = 1
    for message in message_log.messages:
        libtcod.console_set_default_foreground(panel, message.color)
        libtcod.console_print_ex(panel, message_log.x, y, libtcod.BKGND_NONE,libtcod.LEFT, message.text)
        y += 1

    render_bar(panel, 1, 1, bar_width, "HP", player.fighter.hp, player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)

    render_bar(panel, 1, 2, bar_width, "EXP", player.level.current_xp, player.level.experience_to_next_level, libtcod.light_blue, libtcod.darker_blue)

    libtcod.console_print_ex(panel, 1, 4, libtcod.BKGND_NONE, libtcod.LEFT, "Gold: {0}".format(player.fighter.gold))

    if player.inventory.search("Health Talisman") is not None:
        render_bar(panel, 1, 3, bar_width, "Talisman HP", player.fighter.talismanhp, player.fighter.max_hp, libtcod.light_purple, libtcod.darker_purple)

    libtcod.console_print_ex(panel, 1, 5, libtcod.BKGND_NONE, libtcod.LEFT, "Dungeon Level: {0}".format(game_map.dungeon_level))

    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse(mouse, entities, fov_map))

    libtcod.console_blit(panel, 0, 0, screen_width, panel_height, 0, 0, panel_y)

    if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        if game_state == GameStates.SHOW_INVENTORY:
            inventory_title = "Press the key next to an item to use it, or ESC to cancel.\n"
        elif game_state == GameStates.DROP_INVENTORY:
            inventory_title = "Press the key next to an item to drop it, or ESC to cancel.\n"

        inventory_menu(con, inventory_title, player, 50, screen_width, screen_height)

    elif game_state in (GameStates.SHOW_EQUIPMENT_INVENTORY, GameStates.DROP_EQUIPMENT):
        if game_state == GameStates.SHOW_EQUIPMENT_INVENTORY:
            inventory_title = "Press the key next to an item to equip it, or ESC to cancel.\n"
        else:
            inventory_title = "Press the key next to the equipment to drop it, or ESC to cancel.\n"

        equipment_inventory_menu(con, inventory_title, player, 50, screen_width, screen_height)

    elif game_state == GameStates.LEVEL_UP:
        level_up_menu(con, "Level up! Choose a stat to raise:\n", player, 46, screen_width, screen_height)

    elif game_state == GameStates.CHARACTER_SCREEN:
        character_screen(player, 30, 10, screen_width, screen_height)

    elif game_state == GameStates.SHOW_BAG:
        bag_title = "Press the key next to the option to open the bag.\n"

        bag_menu(con, bag_title, player, 50, screen_width, screen_height)

    elif game_state == GameStates.HELP_MENU:
        help_menu(player, 30, 10, screen_width, screen_height)

    elif game_state == GameStates.QUIT_MENU:
        quit_title = "ARE YOU SURE YOU WANT\n  TO QUIT THE GAME?\n"

        quit_menu(con, quit_title, player, 21, screen_width, screen_height)

    elif game_state == GameStates.DROP_MENU:
        drop_title = "Which inventory would you like to drop items from?"

        drop_menu(con, drop_title, player, 50, screen_width, screen_height)


def clear_all(con, entities):
    for entity in entities:
        clear_entity(con, entity)

def draw_entity(con, entity, fov_map, game_map):
    if libtcod.map_is_in_fov(fov_map, entity.x, entity.y) or (entity.stairs and game_map.tiles[entity.x][entity.y].explored):
        libtcod.console_set_default_foreground(con, entity.color)
        libtcod.console_put_char(con, entity.x, entity.y, entity.char, libtcod.BKGND_NONE)


def clear_entity(con, entity):
    libtcod.console_put_char(con, entity.x, entity.y, ' ', libtcod.BKGND_NONE)