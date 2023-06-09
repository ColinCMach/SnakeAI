import torch
import random
import numpy as np
from snake_game import SnakeGameAI, Direction, Point
from collections import deque
from model import Linear_QNet, QTrainer
from helper import plot
MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 # control the randomness
        self.gamma = 0.9 # dis count rate 
        self.memory = deque(maxlen = MAX_MEMORY)# If we exceed the memry it will pop the left 
        self.model = Linear_QNet(11,256,3)
        self.trainer = QTrainer(self.model, lr = LR, gamma = self.gamma)
        # Model , trainer TODO


    def get_state(self,game):
        head = game.snake[0]
        point_l = Point(head.x - 20, head.y)
        point_r = Point(head.x + 20, head.y)
        point_u = Point(head.x, head.y - 20)
        point_d = Point(head.x, head.y +20)

        # initalize direction
        dir_l = game.direction == Direction.LEFT
        dir_r = game.direction == Direction.RIGHT
        dir_u = game.direction == Direction.UP
        dir_d = game.direction == Direction.DOWN

        state = [
            # DANGER IS STRAIGHT
            (dir_r and game.is_collision(point_r)) or 
            (dir_l and game.is_collision(point_l)) or
            (dir_u and game.is_collision(point_u)) or
            (dir_d and game.is_collision(point_d)) ,

            # Danger is right 
            (dir_r and game.is_collision(point_d)) or 
            (dir_l and game.is_collision(point_u)) or
            (dir_u and game.is_collision(point_r)) or 
            (dir_d and game.is_collision(point_l)),

            # Danger is left
            (dir_r and game.is_collision(point_u)) or 
            (dir_l and game.is_collision(point_d)) or 
            (dir_u and game.is_collision(point_l)) or 
            (dir_d and game.is_collision(point_r)),

            # Move Diretion
            dir_l,
            dir_r,
            dir_u,
            dir_d,
            
            #Food Location
            game.food.x < game.head.x, # Food left
            game.food.x > game.head.x, # Food Right
            game.food.y < game.head.y, # Food up
            game.food.y > game.head.y # Food down  


        ]
        return np.array(state, dtype = int)
    
    #### Stop herer
    def remember(self,state, action, reward, next_state, done):
        self.memory.append((state,action, reward, next_state, done)) # pop left is MAX_MEMORY is full

    def train_long_memory(self):
        if len(self.memory) >BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples 
        else:
            mini_sample = self.memory
        
        states, actions , rewards, next_states , dones = zip(*mini_sample)

        self.trainer.train_step(states, actions, rewards, next_states, dones)
    def train_short_memory(self,state, action, reward, next_state, done):
        self.trainer.train_step(state,action,reward,next_state,done)

    def get_action(self, state):
        # Random moves : trade off exploration / exploitation 
        self.epsilon = 80 - self.n_games 
        final_move = [0,0,0]
        if random.randint(0,200) < self.epsilon:
            move = random.randint(0,2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype = torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move

def train():
    plot_scores = []
    plot_mean_scores = []
    total_scores = 0
    record = 0
    agent = Agent()
    game = SnakeGameAI()
    while True:
        # Get old state 
        # Get state returns a tensor of 9 values
        state_old = agent.get_state(game)

        # Get move
        final_move = agent.get_action(state_old)

        #perform and get new state
        reward, done,score = game.play_step(final_move)

        state_new = agent.get_state(game)

        #Train short memory 

        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        #remembetr
        agent.remember(state_old, final_move, reward, state_new, done)

        if done == True:
            # Train lond memory , plot results 
            game.reset()
            agent.n_games += 1 
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print("Game", agent.n_games, "score", score, "record", record)

            plot_scores.append(score)
            total_score = 0
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores,plot_mean_scores)


if __name__ == '__main__':
    train()