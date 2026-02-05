import yaml
from random import choice
from concurrent.futures import ProcessPoolExecutor, as_completed
from environment.env import Environment
from agents.agents import Eater, Seeker

def run_environment(config_path="conf/conf.yaml"):
    # Load configuration
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Initialize environment
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

    
    move_delay = 300
    last_move_time = 0
    game_over = False
    winner = None
    current_time = 0

    # Simulation loop
    while not game_over:
        env.create_graph(
            threat_agents=chasers_list,
            max_threat_level=config["max_threat_level"],
            decay_rate=config["decay_rate"]
        )

        if current_time - last_move_time >= move_delay:
            eater.move(env.current_graph)

            for agent in chasers_list:
                if agent.current_state_duration <= 0:
                    agent.current_state = choice([state for state in agent.states if state != agent.current_state])
                    agent.reset_current_state_duration()

                agent.move(env.current_graph, eater.current_position)
                agent.current_state_duration -= 1

                if agent.current_position == eater.current_position:
                    game_over = True
                    winner = "chaser"
                    break

            if not game_over:
                y, x = eater.current_position
                env.grid[y][x].has_pellet = False

            last_move_time = current_time

        nodes_with_pellets = [node for node in env.current_graph.keys() if env.current_graph[node].has_pellet]
        if len(nodes_with_pellets) == 0:
            game_over = True
            winner = "eater"

        current_time += 50

    return winner


def run_simulations_parallel(num_simulations=100, config_path="conf/conf.yaml"):
    results = {"eater": 0, "chaser": 0}

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_environment, config_path) for _ in range(num_simulations)]

        for future in as_completed(futures):
            winner = future.result()
            results[winner] += 1

    return results


if __name__ == "__main__":
    num_simulations = 100  
    max_workers = None     
    results = {"eater": 0, "chaser": 0}
    with ProcessPoolExecutor(max_workers=max_workers) as executor:        
        futures = [executor.submit(run_environment) for _ in range(num_simulations)]        
        for future in as_completed(futures):
            winner = future.result()
            results[winner] += 1
    print(f"Results after {num_simulations} simulations: {results}")


