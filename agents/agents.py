import random
import string
import pygame as pg
import heapq 


pg.init()
    
class Agent:
    """
    Base class for all agents in the environment.

    Attributes:
        current_position (tuple[int, int]): Current (row, column) position.
        enviroment: Reference to the environment object containing the grid.
        directions (dict): Mapping of direction indices to names.
        states (list[str]): Possible agent states.
        current_state (str): Active state.
        color (tuple[int, int, int]): RGB color used for rendering.             
    """

    def __init__(self, row, column, enviroment):
        self.name = self._generate_random_name()
        self.current_position = (row, column)
        self.enviroment = enviroment
        self.directions = {0: "up", 1: "right", 2: "down", 3: "left"}
        self.states = []
        self.current_state = ""
        self.color = (random.randint(100,255), random.randint(0,100), random.randint(0,100))
        
    def _generate_random_name(self):
        vowels = "aeiou"
        consonants = "".join([c for c in string.ascii_lowercase if c not in vowels])        
        # Pattern: C V C V C 
        name = ""
        for i in range(5):
            if i % 2 == 0:  
                name += random.choice(consonants)
            else:           
                name += random.choice(vowels)                
        return name.capitalize()

    def move(self):
        """
        Defines agent movement behavior.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement move()")

    def _check_valid_movement(self, next_position):
        """
        Checks whether a target position is walkable.

        Args:
            next_position (tuple[int, int]): Target (row, column).

        Returns:
            bool: True if movement is valid, False otherwise.
        """
        row, col = next_position
        try:
            return self.enviroment.grid[row][col].walkable
        except IndexError:
            return False

    def draw(self, screen):
        """
        Draws the agent as a circle centered in its current tile.
        """
        tile = self.enviroment.grid[self.current_position[0]][self.current_position[1]]
        center_x = tile.rect.x + tile.rect.width // 2
        center_y = tile.rect.y + tile.rect.height // 2
        radius = tile.rect.width // 2
        pg.draw.circle(screen, self.color, (center_x, center_y), radius)


class Eater(Agent):
    """
    Agent that searches for and moves toward pellets.

    Uses the A* pathfinding algorithm to select the next move
    toward the nearest pellet while considering threat levels.
    """

    def __init__(self, row, column, enviroment):
        super().__init__(row, column, enviroment)           
        self.states = ["eat"]
        self.current_state = "eat"
        self.color = (255,255,0)

    def move(self, graph):
        """
        Executes one movement step based on the current state.

        Args:
            graph (dict): Graph representation of the grid where
                          keys are positions and values are node objects.
        """
        if self.current_state == "eat":
            next_position = self._eat_pellets(graph)

        if self._check_valid_movement(next_position):
            self.current_position = next_position

    def _eat_pellets(self, graph):
        """
        A* SEARCH ALGORITHM

        Finds the optimal next move toward the closest pellet.

        Cost function:
            f(n) = g(n) + h(n) + threat_level

        where:
            g(n) = distance from start
            h(n) = Manhattan distance to nearest pellet
            threat_level = extra penalty for dangerous tiles

        Args:
            graph (dict): Grid graph with adjacency and tile metadata.

        Returns:
            tuple[int, int]: Next position to move to.
        """

        starting_position = self.current_position

        # Priority queue for open nodes (min-heap)
        open_list = []

        # Stores the best previous node for each visited node
        path = {}

        # g(n): cost from start to node
        cost_values = {starting_position: 0}

        heapq.heappush(open_list, (0, starting_position))

        # Collect all pellet locations
        nodes_with_pellets = [
            node for node in graph.keys() if graph[node].has_pellet
        ]

        while open_list:
            current_priority, current_node = heapq.heappop(open_list)

            # Goal condition: pellet found
            if graph[current_node].has_pellet:
                break

            for adjacent_tile in graph[current_node].adjacent_tiles:
                new_cost = cost_values[current_node] + 1

                # Relaxation step
                if (adjacent_tile not in cost_values or new_cost < cost_values[adjacent_tile]):
                    cost_values[adjacent_tile] = new_cost
                    path[adjacent_tile] = current_node

                    # Heuristic: distance to closest pellet
                    h = min(abs(adjacent_tile[0] - pellet[0]) + abs(adjacent_tile[1] - pellet[1]) for pellet in nodes_with_pellets) 
                    priority = (new_cost + h + (graph[adjacent_tile].threat_level * 10000)) # Extra weight for threat level
                    heapq.heappush(open_list, (priority, adjacent_tile))

        target = current_node

        # If already on a pellet, stay in place
        if target == starting_position:
            return starting_position

        # Backtrack to find the next step from the start
        next_move = target
        while path[next_move] != starting_position:
            next_move = path[next_move]

        return next_move      
        
    
class Seeker(Agent):
    def __init__(self, row, column, enviroment):
       super().__init__(row, column, enviroment)    
       self.states = ["search","idle"]
       self.current_state = "idle"
       self.current_state_duration = random.randint(20,70) # In number of movements
       
    def reset_current_state_duration(self):
        self.current_state_duration = random.randint(20,70) # In number of movements
       
    def move(self, graph, eater_position):
        if self.current_state == "idle":
            self.current_position = self._move_random(graph)    
        
        if self.current_state == "search":
            self.current_position = self._search_eater(graph, eater_position)           

        
    def _move_random(self,graph): 
        can_move = False               
        while can_move == False:
            direction = self.directions[random.randint(0,3)]            
            if direction == "up":
                next_move = (self.current_position[0] - 1, self.current_position[1])
            elif direction == "right":
                next_move = (self.current_position[0], self.current_position[1] + 1)
            elif direction == "down":
                next_move = (self.current_position[0] + 1, self.current_position[1])
            elif direction == "left":
                next_move = (self.current_position[0], self.current_position[1] - 1)           
            can_move = self._check_valid_movement(next_move)       
        return next_move
    
    
    def _search_eater(self, graph, eater_position):
        
        """
        A* SEARCH ALGORITHM

        Finds the optimal next move toward the closest pellet.

        Cost function:
            f(n) = g(n) + h(n)

        where:
            g(n) = distance from start
            h(n) = Manhattan distance to nearest pellet            

        Args:
            eater_position (tuple): Current position attribute from eater
            graph (dict): Grid graph with adjacency and tile metadata.

        Returns:
            tuple[int, int]: Next position to move to.
        """
        
        starting_position = self.current_position
    
        # Priority queue for open nodes (min-heap)
        open_list = []
    
        # Stores the best previous node for each visited node
        path = {}
    
        # g(n): cost from start to node
        cost_values = {starting_position: 0}
    
        heapq.heappush(open_list, (0, starting_position))   
    
        while open_list:
            current_priority, current_node = heapq.heappop(open_list)
    
            # Goal condition: pellet found
            if graph[current_node].coord == eater_position:
                break
    
            for adjacent_tile in graph[current_node].adjacent_tiles:
                new_cost = cost_values[current_node] + 1
    
                # Relaxation step
                if (adjacent_tile not in cost_values or new_cost < cost_values[adjacent_tile]):
                    cost_values[adjacent_tile] = new_cost
                    path[adjacent_tile] = current_node
    
                    # Heuristic: distance to closest pellet
                    h = abs(adjacent_tile[0] - eater_position[0]) + abs(adjacent_tile[1] - eater_position[1])
    
                    priority = (new_cost + h)
    
                    heapq.heappush(open_list, (priority, adjacent_tile))
    
        target = current_node
    
        # If already on eater, stay in place
        if target == starting_position:
            return starting_position
    
        # Backtrack to find the next step from the start
        next_move = target
        while path[next_move] != starting_position:
            next_move = path[next_move]
    
        return next_move    
        