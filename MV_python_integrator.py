# -*- coding: utf-8 -*-

import sys
from py4j.java_gateway import JavaGateway, GatewayParameters, CallbackServerParameters

import des_lp

class SimulationWrapper(object):

	# constructor for Python
	def __init__(self, model):
		self.model = model

	# code to let multivesta initialize the simulator for a new simulation
	# that is, re-initialize the model to its initial state, and set the
	# new random seed
	def setSimulatorForNewSimulation(self, random_seed):
		self.model.init(random_seed)	
			#Here you should replace 'setSimulatorForNewSimulation(random_seed)' 
			# with a method of your model to 
			#- set the new nuovo random seed
			#- reset the status of the model to the initial one
			#

	# code to let multivesta ask the simulator to perform a step of simulation
	def performOneStepOfSimulation(self):
		self.model.one_step()

	# code to let multivesta ask the simulator to perform a "whole simulation"
        # bart: it seems to be never used
	def performWholeSimulation(self):
		self.model.performWholeSimulation()

	# code to let multivesta ask the simulator the current simulated time
	def getTime(self):
		return float(self.model.getTime())

	# code to let multivesta ask the simulator to return the value of the
	# specified observation in the current state of the simulation
	def rval(self, observation):
		# print(f"-> rval observation {observation} (s.rval(4) = {self.model.eval(4)})")
		return self.model.eval(observation)

	class Java:
		implements = ['vesta.python.IPythonSimulatorWrapper']


if __name__ == '__main__':
	porta = int(sys.argv[1])
	callback_porta = int(sys.argv[2])
	print('Python engine: expecting connection with java on port: '+str(porta)+' and callback connection on port '+str(callback_porta))
	gateway = JavaGateway(start_callback_server=True,gateway_parameters=GatewayParameters(port=porta),callback_server_parameters=CallbackServerParameters(port=callback_porta))
	
	#Here you should put any initialization code you need to create an instance of
	#your model_file_name class
	
	model=des_lp.Model()
	gateway.entry_point.playWithState(SimulationWrapper(model))
