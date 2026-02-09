import sys
import pygame as pg
import yaml
from environment.env import Environment
from agents.agents import Eater, Seeker
from random import choice

if not pg.font:
    print("Warning, fonts disabled")
if not pg.mixer:
    print("Warning, sound disabled")
    
pg.init()

with open("conf/conf.yaml") as f:
    config = yaml.safe_load(f)

                    
env = Environment()
env.fill_matrix(config["height"], config["width"], config["tile_size"])
env.load_layout(config["default_layout"])   
walkable_tiles = [tile for row in env.grid for tile in row if tile.walkable]      
        
eater_spawn_tile = choice(walkable_tiles) 
eater = Eater(eater_spawn_tile.y, eater_spawn_tile.x, env)
chasers_list = []
for agent in range(config["amount_of_seekers"]):
    chaser_spawn_tile = choice(walkable_tiles)  
    chasers_list.append(Seeker(chaser_spawn_tile.y, chaser_spawn_tile.x, env))  

# --- Setup display ---
information_panel_width = 300
screen = pg.display.set_mode(((config["width"] * config["tile_size"]) + information_panel_width, config["height"] * config["tile_size"]))
pg.display.set_caption("Grid with Walls")

clock = pg.time.Clock()
last_move_time = 0 
move_delay = 200 # Increase to speed down



DEBUG = True  
font = pg.font.SysFont(None, 25)

running = True
game_over = False

while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
            
    if not game_over:
      
        # Draw Grid
        screen.fill(tuple(config["background_color"]))           
        for y in range(config["height"]):
            for x in range(config["width"]):
                tile = env.grid[y][x]
    
                # Draw walkable/unwalkable tiles
                if not tile.walkable:
                    pg.draw.rect(screen, tuple(config["unwalkable_tile_color"]), tile.rect)
                else:
                    pg.draw.rect(screen, tuple(config["walkable_tile_color"]), tile.rect)
    
                # Draw pellets
                if tile.has_pellet:
                    center_x = tile.rect.x + tile.rect.width // 2
                    center_y = tile.rect.y + tile.rect.height // 2
                    radius = tile.rect.width // 6
                    pg.draw.circle(screen, tuple(config["pellet_color"]), (center_x, center_y), radius)
    
                # DEBUG: overlay threat heatmap
                if DEBUG and tile.walkable and env.current_graph:
                    node = env.current_graph.get((y, x))
                    if node:
                        intensity = int((node.threat_level / config["max_threat_level"]) * 255)
                        intensity = max(0, min(intensity, 255))
                        heat_surface = pg.Surface((tile.rect.width, tile.rect.height), pg.SRCALPHA)
                        heat_surface.fill((intensity, 0, 0, 255))
                        screen.blit(heat_surface, (tile.rect.x, tile.rect.y))      
                        text = font.render("", True, (255, 255, 255))
                        screen.blit(text, (tile.rect.x + 2, tile.rect.y + 2))
    
        # Update graph with current seekers positions and threat levels
        env.create_graph(threat_agents = chasers_list, max_threat_level = config["max_threat_level"], decay_rate = config["decay_rate"])
    
        # Move agents with time delay        
        current_time = pg.time.get_ticks()
        
        if current_time - last_move_time >= move_delay:            
            eater.move(env.current_graph)    
            for agent in chasers_list:
                if agent.current_state_duration <= 0:
                    agent.current_state = choice([state for state in agent.states if state != agent.current_state])           
                    agent.reset_current_state_duration()
                agent.move(env.current_graph, eater.current_position)
                agent.current_state_duration -= 1                    
                
                # Check if this chaser collided with the eater after moving
                if agent.current_position == eater.current_position:
                    game_over = True
                    winner = "chaser"                    
                    break
    
            # Eater consumes pellet
            if not game_over:   
               env.grid[eater.current_position[0]][eater.current_position[1]].has_pellet = False
    
            last_move_time = current_time
    
        # Draw agents
        eater.draw(screen)        
        for agent in chasers_list:
            agent.draw(screen)
            
        # Count pellets. If no pelles then eater wins
        nodes_with_pellets = []
        for node in env.current_graph.keys():
            if env.current_graph[node].has_pellet :
                nodes_with_pellets.append(node)
        if len(nodes_with_pellets) == 0:
            game_over = True
            winner = "eater"
            break
            
        # Check if eater and chaser share position. If they do eater losses       
        for chaser in chasers_list:
            if eater.current_position == chaser.current_position:
                game_over = True
                winner = "chaser"
                break
                
                
        # Draw Panel Information        
        circle_radius = 8  # size of the color circle
        circle_margin = 5  # space between circle and text
        space_between_lines = 60
        
       
        all_agents = [eater] + chasers_list        
        for i, agent in enumerate(all_agents):
            y = 200 + i * space_between_lines  # vertical position
        
            # Draw color circle
            information_panel_starting_x = 730 # horizontal position
            information_panel_starting_y = y
            pg.draw.circle(screen, agent.color, (information_panel_starting_x, information_panel_starting_y), circle_radius)
        
            # Draw agent name and state
            text = font.render(f"{agent.name}: {agent.current_state}", True, (0, 0, 0))
            text_rect = text.get_rect(midleft=(information_panel_starting_x + circle_radius + circle_margin, y))
            screen.blit(text, text_rect)    
            


    if game_over:           
        if winner == "eater":     
            game_over_message = "Eater Won"
        elif winner == "chaser":     
            game_over_message = "chaser Won"        
        text = font.render(game_over_message, True, (255, 0, 0))
        text_rect = text.get_rect(center=(320, 240))
        screen.blit(text, text_rect)   
        
    pg.display.flip()
    clock.tick(60)    
        

pg.quit()
sys.exit()






