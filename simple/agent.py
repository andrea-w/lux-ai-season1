# for kaggle-environments
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from random import randint
import math
import sys

### Define helper functions

# this snippet finds all resources stored on the map and puts them into a list so we can search over them
def find_resources(game_state):
    resource_tiles: list[Cell] = []
    width, height = game_state.map_width, game_state.map_height
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
    return resource_tiles

# the next snippet finds the closest resources that we can mine given position on a map
def find_closest_resources(pos, player, resource_tiles, unit_positions):
    unit_positions_without_pos = unit_positions
    unit_positions_without_pos.remove(pos)
    for resource_tile in resource_tiles:
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and player.researched_uranium():
            return find_closest_uranium(pos, resource_tiles, unit_positions_without_pos)
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and player.researched_coal():
            return find_closest_coal(pos, resource_tiles, unit_positions_without_pos)
        return find_closest_wood(pos, resource_tiles, unit_positions_without_pos)

def find_closest_coal(pos, resource_tiles, unit_positions):
    closest_dist = math.inf
    closest_coal_tile = None
    for resource_tile in resource_tiles:
        if resource_tile.resource.type != Constants.RESOURCE_TYPES.COAL:
            continue
        dist = resource_tile.pos.distance_to(pos)
        move_direction = pos.direction_to(resource_tile.pos)
        unit_new_pos = pos.translate(move_direction, 1)
        if dist < closest_dist and resource_tile.pos not in unit_positions and unit_new_pos not in unit_positions:
            closest_dist = dist
            closest_coal_tile = resource_tile
    unit_positions.append(unit_new_pos)
    return (closest_coal_tile, unit_positions)

def find_closest_uranium(pos, resource_tiles, unit_positions):
    closest_dist = math.inf
    closest_uranium_tile = None
    for resource_tile in resource_tiles:
        if resource_tile.resource.type != Constants.RESOURCE_TYPES.URANIUM:
            continue
        dist = resource_tile.pos.distance_to(pos)
        move_direction = pos.direction_to(resource_tile.pos)
        unit_new_pos = pos.translate(move_direction, 1)
        if dist < closest_dist and resource_tile.pos not in unit_positions and unit_new_pos not in unit_positions:
            closest_dist = dist
            closest_uranium_tile = resource_tile
    unit_positions.append(unit_new_pos)
    return (closest_uranium_tile, unit_positions)

def find_closest_wood(pos, resource_tiles, unit_positions):
    closest_dist = math.inf
    closest_wood_tile = None
    for resource_tile in resource_tiles:
        if resource_tile.resource.type != Constants.RESOURCE_TYPES.WOOD:
            continue
        dist = resource_tile.pos.distance_to(pos)
        move_direction = pos.direction_to(resource_tile.pos)
        unit_new_pos = pos.translate(move_direction, 1)
        if dist < closest_dist and resource_tile.pos not in unit_positions and unit_new_pos not in unit_positions:
            closest_dist = dist
            closest_wood_tile = resource_tile
    unit_positions.append(unit_new_pos)
    return (closest_wood_tile, unit_positions)

def find_closest_city_tile(pos, player):
    closest_city_tile = None
    if len(player.cities) > 0:
        closest_dist = math.inf
        # the cities are stored as a dictionary mapping city id to the city object, which has a citytiles field that
        # contains the information of all citytiles in that city
        for k, city in player.cities.items():
            for city_tile in city.citytiles:
                dist = city_tile.pos.distance_to(pos)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_city_tile = city_tile
    return closest_city_tile

# returns boolean
def should_build_another_citytile(player):
    total_citytiles = 0
    for city in player.cities.values():
        total_citytiles += len(city.citytiles)
    if len(player.units) == total_citytiles:
        return True
    
    for city in player.cities.values():
        if city.fuel <= city.get_light_upkeep() * 10:
            return False

    return True

def get_city_with_least_fuel(cities):
    lowest_fuel = math.inf
    lowest_fuel_city = None
    for city in cities.values():
        if city.fuel < lowest_fuel:
            lowest_fuel = city.fuel
            lowest_fuel_city = city
    return (lowest_fuel_city, lowest_fuel)

def pick_random_direction():
    meh = randint(0, 4)
    if meh == 0:
        return Constants.DIRECTIONS.CENTER
    elif meh == 1:
        return Constants.DIRECTIONS.EAST
    elif meh == 2:
        return Constants.DIRECTIONS.NORTH
    elif meh == 3:
        return Constants.DIRECTIONS.SOUTH
    elif meh == 4:
        return Constants.DIRECTIONS.WEST

def city_can_build_cart_or_worker(player):
    total_citytiles = 0
    for c in player.cities.values():
        total_citytiles += len(c.citytiles)
    if len(player.units) < total_citytiles:
        return True
    return False

game_state = None
def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    resource_tiles = find_resources(game_state)

    unit_positions = []
    for unit in player.units:
        unit_positions.append(unit.pos)
    
    for unit in player.units:
        # if the unit is a worker (can mine resources) and can perform an action this turn
        if unit.is_worker() and unit.can_act():
            # we want to mine only if there is space left in the worker's cargo
            if unit.get_cargo_space_left() > 0:
                # find the closest resource if it exists to this unit
                closest_resource_tile, unit_positions = find_closest_resources(unit.pos, player, resource_tiles, unit_positions)
                if closest_resource_tile is not None:
                    # create a move action to move this unit in the direction of the closest resource tile and add to our actions list
                    move_direction = unit.pos.direction_to(closest_resource_tile.pos)
                    action = unit.move(move_direction)
                    unit_positions.append(unit.pos.translate(move_direction, 1))
                    actions.append(action)
                else:
                    closest_city_tile = find_closest_city_tile(unit.pos, player)
                    move_direction = unit.pos.direction_to(closest_city_tile.pos)
                    action = unit.move(move_direction)
                    unit_positions.append(unit.pos.translate(move_direction, 1))
                    actions.append(action)
            else:
                lowest_fuel_city, lowest_fuel = get_city_with_least_fuel(player.cities)
                if lowest_fuel <= 230:
                    action = unit.move(unit.pos.direction_to(lowest_fuel_city.citytiles[0].pos))
                    actions.append(action)
                elif unit.pos.distance_to(lowest_fuel_city.citytiles[0].pos) > 0.25 * game_state.map_height:
                    if unit.can_build(game_state.map):
                        actions.append(unit.build_city())
                    else:
                        actions.append(unit.move(pick_random_direction()))
                elif should_build_another_citytile(player):
                    if unit.can_build(game_state.map):
                        actions.append(unit.build_city())
                    else:
                        actions.append(unit.move(pick_random_direction()))
                else:
                    # find the closest citytile and move the unit towards it to drop resources to a citytile to fuel the city
                    closest_city_tile = find_closest_city_tile(unit.pos, player)
                    if closest_city_tile is not None:
                        # create a move action to move this unit in the direction of the closest resource tile and add to our actions list
                        move_direction = unit.pos.direction_to(closest_city_tile.pos)
                        action = unit.move(move_direction)
                        unit_positions.append(unit.pos.translate(move_direction, 1))
                        actions.append(action)
        elif unit.is_cart() and unit.can_act():
            if unit.get_cargo_space_left() > 20:
                closest_resource_tile, unit_positions = find_closest_resources(unit.pos, player, resource_tiles, unit_positions)
                if closest_resource_tile is not None:
                    move_direction = unit.pos.direction_to(closest_resource_tile.pos)
                    action = unit.move(move_direction)
                    unit_positions.append(unit.pos.translate(move_direction, 1))
                    actions.append(action)
            else:
                closest_city_tile = find_closest_city_tile(unit.pos, player)
                if closest_city_tile is not None:
                    move_direction = unit.pos.direction_to(closest_city_tile.pos)
                    actions.append(unit.move(move_direction))
                    unit_positions.append(unit.pos.translate(move_direction, 1))
    
    for city in player.cities.values():
        for city_tile in city.citytiles:
            if city_tile.can_act():
                if city_can_build_cart_or_worker(player):
                    actions.append(city_tile.build_worker())
                else:
                    actions.append(city_tile.research())

    return actions
