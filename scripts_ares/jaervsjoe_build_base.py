from dto.action_base_dto import ActionBaseDto
from helper_functions.obs_helper import get_current_state, get_random_unit, get_count_unit, base_is_upper_left
from helper_functions.point_rect import Point

from pysc2.lib import actions, features, units

_NOT_QUEUED = [0]
_QUEUED = [1]
_SELECT_ALL = [2]


_NO_OP = actions.FUNCTIONS.no_op.id
_SELECT_POINT = actions.FUNCTIONS.select_point.id
_BUILD_SUPPLY_DEPOT = actions.FUNCTIONS.Build_SupplyDepot_screen.id
_BUILD_BARRACKS = actions.FUNCTIONS.Build_Barracks_screen.id
_TRAIN_MARINE = actions.FUNCTIONS.Train_Marine_quick.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_ATTACK_MINIMAP = actions.FUNCTIONS.Attack_minimap.id
_HARVEST_GATHER = actions.FUNCTIONS.Harvest_Gather_screen.id

class JaervsjoeBuildBase:
    def __init__(self):
        #keep track of what action we are performin right now
        self.previous_action = None   
        self.move_number = 0

        #episode related
        self.camera_position_start = None
        self.position_cc_start = None

    def act_build_base(self, current_state_others):
        #TODO: build command center
        command_center_count = current_state_others[0]
        supply_depot_count = current_state_others[1]
        barracks_count = current_state_others[2]
        army_supply_count = current_state_others[3]
        # resources = current_state[4]

        # cost_command_center = 100
        # cost_supply_depot = 100
        # cost_barracks = 100
        if command_center_count < 0:
            return ActionBaseDto.build_command_center()
        if supply_depot_count < 0.9:
            return ActionBaseDto.build_supply_depot()
        if barracks_count < 0.9:
            return ActionBaseDto.build_barracks()
        if army_supply_count < 1:
            return ActionBaseDto.build_marine()

        return ActionBaseDto.do_nothing()

    def moveNumberZeroZero(self, obs):
        current_state = get_current_state(obs)
        smart_action = self.act_build_base(current_state["state_others"])
        self.previous_action = smart_action
        if actions.FUNCTIONS.move_camera.id in obs.observation['available_actions']:
            if smart_action == ActionBaseDto.build_barracks() or smart_action == ActionBaseDto.build_supply_depot() or smart_action == ActionBaseDto.build_command_center():
                return actions.FUNCTIONS.move_camera((self.camera_position_start.x, self.camera_position_start.y))
        else: 
            print("could not move camera, available actions are " + str(obs.observation['available_actions']))
                
        return actions.FunctionCall(actions.FUNCTIONS.no_op.id, [])


    def moveNumberZero(self, obs):      
        if obs.last():
            raise Exception('last frame, not defined')
        smart_action = self.previous_action
        if smart_action == ActionBaseDto.build_barracks() or smart_action == ActionBaseDto.build_supply_depot() or smart_action == ActionBaseDto.build_command_center():
            cam_position = Point((obs.observation["camera_position"][0]/3)*2, (obs.observation["camera_position"][1]/3)*2)
            if(abs(cam_position.x - self.camera_position_start.x) > 1 or abs(cam_position.y - self.camera_position_start.y) > 1):
                print("wrong position to build building")
                return actions.FunctionCall(actions.FUNCTIONS.no_op.id, [])

            scv = get_random_unit(obs, units.Terran.SCV)

            if(scv is  None):    
                return actions.FunctionCall(actions.FUNCTIONS.no_op.id, [])

            x = scv.x
            y = scv.y
            #TODO: same for larger than...
            if(x < 0 or y < 0):
                return actions.FunctionCall(actions.FUNCTIONS.no_op.id, [])

            return actions.FUNCTIONS.select_point("select", (scv.x, scv.y))
            
        elif smart_action == ActionBaseDto.build_marine():
            barrack = get_random_unit(obs, units.Terran.Barracks)
            if(barrack is not None):
                return actions.FUNCTIONS.select_point("select_all_type", (barrack.x, barrack.y))

        return actions.FunctionCall(actions.FUNCTIONS.no_op.id, [])


    def moveNumberOne(self, obs):        
        smart_action = self.previous_action
        commCenter = get_random_unit(obs, units.Terran.CommandCenter)
        # if commCenter is None:
        #     return actions.FunctionCall(actions.FUNCTIONS.no_op.id, [])
        # assert commCenter.x > 0
        if smart_action == ActionBaseDto.build_barracks() or smart_action == ActionBaseDto.build_supply_depot() or smart_action == ActionBaseDto.build_command_center():
            cam_position = Point((obs.observation["camera_position"][0]/3)*2, (obs.observation["camera_position"][1]/3)*2)
            if(abs(cam_position.x - self.camera_position_start.x) > 1 or abs(cam_position.y - self.camera_position_start.y) > 1):
                print("wrong position to build building")
                return actions.FunctionCall(actions.FUNCTIONS.no_op.id, [])        

        if smart_action == ActionBaseDto.build_supply_depot():
            if (actions.FUNCTIONS.Build_SupplyDepot_screen.id in obs.observation.available_actions):
                if commCenter is not None:
                    supply_depot_count = get_count_unit(obs, units.Terran.SupplyDepot)
                    if supply_depot_count == 0:
                        target = self.transform_distance(round(commCenter.x), -35, round(commCenter.y), 0, base_is_upper_left(obs))
                        return actions.FUNCTIONS.Build_SupplyDepot_screen("now", target)
                    elif supply_depot_count == 1:
                        target = self.transform_distance(round(commCenter.x), -25, round(commCenter.y), -25, base_is_upper_left(obs))
                        return actions.FUNCTIONS.Build_SupplyDepot_screen("now", target)
                    elif supply_depot_count == 2:
                        target = self.transform_distance(round(commCenter.x), -30, round(commCenter.y), -15, base_is_upper_left(obs))
                        return actions.FUNCTIONS.Build_SupplyDepot_screen("now", target)                    

        elif smart_action == ActionBaseDto.build_barracks():
            barracks_count = get_count_unit(obs, units.Terran.Barracks)
            if barracks_count < 2 and actions.FUNCTIONS.Build_Barracks_screen.id in obs.observation.available_actions:
                if commCenter is not None:
                    if  barracks_count == 0:
                        target = self.transform_distance(round(commCenter.x), 15, round(commCenter.y), -9, base_is_upper_left(obs))
                    elif  barracks_count == 1:
                        target = self.transform_distance(round(commCenter.x), 15, round(commCenter.y), 12, base_is_upper_left(obs))

                    return actions.FUNCTIONS.Build_Barracks_screen("now", target)
        
        elif smart_action == ActionBaseDto.build_command_center():
            if actions.FUNCTIONS.Build_CommandCenter_screen.id in obs.observation.available_actions:
                return actions.FUNCTIONS.Build_CommandCenter_screen("now", [self.position_cc_start.x, self.position_cc_start.y])


        elif smart_action == ActionBaseDto.build_marine():
            if _TRAIN_MARINE in obs.observation['available_actions']:
                return actions.FunctionCall(_TRAIN_MARINE, [_QUEUED])
    
        return actions.FunctionCall(actions.FUNCTIONS.no_op.id, [])

    def moveNumberTwo(self, obs):
        smart_action = self.previous_action
            
        if smart_action == ActionBaseDto.build_barracks() or smart_action == ActionBaseDto.build_supply_depot():
            if (actions.FUNCTIONS.Harvest_Gather_screen.id in obs.observation.available_actions):
                mineral_field = get_random_unit(obs, units.Neutral.MineralField)
                if mineral_field is not None:
                    return actions.FunctionCall(_HARVEST_GATHER, [_QUEUED, [mineral_field.x, mineral_field.y]])

        return actions.FunctionCall(_NO_OP, [])

    def transform_distance(self, x, x_distance, y, y_distance, base_top_left):
        if not base_top_left:
            return [x - x_distance, y - y_distance]
        
        return [x + x_distance, y + y_distance]

