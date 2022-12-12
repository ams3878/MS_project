class ControlBaseClass():
	def __init__(self):
		self.controls_data = None # this will be the input and out structure
	def send_controls(self):
		pass

class ARkitControls(ControlBaseClass):
	def __init__(self, out_fn):
		super().__init__()
		self.out_file = open(out_fn, "w")
		self.set_bshapes_to_controls()

	def send_controls(self, frame):
		wrtstr_out = f"{frame} "
		for v in self.controls_data:
			wrtstr_out += f"{v[2]} " if v[1] != -1 else f"{-1} "

		self.out_file.write(wrtstr_out + "\n")

	def set_bshapes_to_controls(self):
		self.controls_data  = [
		["eyeBlinkLeft",[(7,1.0)],0],
		["eyeLookDownLeft",[-1],0],
		["eyeLookInLeft",[-1],0],
		["eyeLookOutLeft",[-1],0],
		["eyeLookUpLeft",[-1],0],
		["eyeSquintLeft",[-1],0],
		["eyeWideLeft",[(7,.333),(1,.333),(3,.333)],0],
		["eyeBlinkRight",[(8,1.0)],0],
		["eyeLookDownRight",[-1],0],
		["eyeLookInRight",[-1],0],
		["eyeLookOutRight",[-1],0],
		["eyeLookUpRight",[-1],0],
		["eyeSquintRight",[-1],0],
		["eyeWideRight",[(8,.333),(2,.333),(4,.333)],0],
		["jawForward",[-1],0],
		["jawLeft",[-1],0],
		["jawRight",[-1],0],
		["jawOpen",[(51,1.0)],0],
		["mouthClose",[-1],0],
		["mouthFunnel",[(51,.333),(35,.333),(36,.333)],0],
		["mouthPucker",[(35,.5),(36,.5)],0],
		["mouthLeft",[(23,1.0)],0],
		["mouthRight",[(24,1.0)],0],
		["mouthSmileLeft",[(23,.5),(25,.5)],0],
		["mouthSmileRight",[(24,.5),(26,.5)],0],
		["mouthFrownLeft",[(29,1.0)],0],
		["mouthFrownRight",[(30,1.0)],0],
		["mouthDimpleLeft",[(27,1.0)],0],
		["mouthDimpleRight",[(28,1.0)],0],
		["mouthStretchLeft",[(39,1.0)],0],
		["mouthStretchRight",[(40,1.0)],0],
		["mouthRollLower",[-1],0],#au 28
		["mouthRollUpper",[-1],0],#au 28
		["mouthShrugLower",[-1],0],
		["mouthShrugUpper",[(19,.5),(20,.5)],0],
		["mouthPressLeft",[(25,.333),(31,.333),(19,.333)],0],
		["mouthPressRight",[(26,.333),(32,.333),(20,.333)],0],
		["mouthLowerDownLeft",[-1],0],
		["mouthLowerDownRight",[-1],0],
		["mouthUpperUpLeft",[-1],0],
		["mouthUpperUpRight",[-1],0],
		["browDownLeft",[-1],0],
		["browDownRight",[-1],0],
		["browInnerUp",[(1,.5),(2,.5)],0],
		["browOuterUpLeft",[(3,1.0)],0],
		["browOuterUpRight",[(4,1.0)],0],
		["cheekPuff",[-1],0],
		["cheekSquintLeft",[-1],0],
		["cheekSquintRight",[-1],0],
		["noseSneerLeft",[-1],0],
		["noseSneerRight",[-1],0]]
