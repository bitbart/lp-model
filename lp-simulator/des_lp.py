import random
from datetime import datetime

from blockchain import *
from lp import *

class Model:

    def init(self, random_seed):
        random.seed(random_seed) # ideally, random_seed = datetime.now()

        # Number of steps in the simulation
        self.t = 0
        
        # number of steps in the simulation
        self.N_STEPS = 1000

        # Create a new blockchain instance
        self.bc = Blockchain()

        # Liquidator
        self.bc.faucet("A", 1000, "T0")
        self.init_Wliq = self.bc.net_worth("A")
        self.bc.deposit("A", 900, "T0")

        # Borrower
        self.bc.faucet("B", 100, "T1")
        self.bc.deposit("B", 100, "T1")
    

    # code to let MultiVeStA ask the simulator to perform a step of simulation
    def one_step(self):
        # LP actions:
        # 0 -> B borrows
        # 1 -> accrue interest
        # 2 -> A liquidates
        # 3 -> set price

        b = random.randint(0,3)

        if (b==0):
            amt = random.randint(1,10)
            self.bc.borrow("B", 5, "T0")

        elif b==1:
            self.bc.accrue_interest()

        elif b==2:
            self.bc.lp.liquidate("A", 1, "T0", "B", "T1")

        self.t += 1
        # print(f"x={self.x},t={self.t}")

    def performWholeSimulation(self):
        while (self.t < self.N_STEPS):
            self.one_step()

    def getTime(self):
        return float(self.t)

    # code to let MultiVeStA ask the simulator to return the value of the
    # specified observation in the current state of the simulation
    def eval(self, obs):
        # bart: obs 0,1,2 seem to be reserved by MultiVeStA

        # obs 4 = number of steps performed in the simulation
        if (obs==4):
            val = float(self.t)

        # obs 5 = health factor of the borrower B
        elif (obs==5):
            val = float(self.bc.lp.health_factor("B"))

        # obs 6 = gain of the liquidator A
        elif (obs==6):
            val = float(self.bc.net_worth("A") - self.init_Wliq)

        else:
            val = float(42)

        # print(f"<- eval({obs}) = {val}")
        return val
