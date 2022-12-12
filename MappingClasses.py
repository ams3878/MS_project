import sys
import dlib
import numpy as np

class FacialMapping:
	def __init__(self):
		self.mapping = None  # some storage for data, dictionary likely best option here
		self.capture_object = None
		self.control_object = None
		self.frame_number = 0

	def create_map_geometry(self):
		pass
	def init_map_input(self):
		pass
	def init_map_output(self):
		pass
	def get_input_frame(self):
		pass
	def calibrate_mapping(self):
		pass
	def calculate_deltas(self):
		pass


class FACS(FacialMapping):
	def __init__(self, num_AU=29, num_anchors=4, au_file="FACS_aus"):
		super().__init__()
		self.num_AUs = num_AU
		self.num_anchors = num_anchors
		self.au_list_size = num_AU * 2

		self.input_indices = [0] * self.au_list_size
		self.AU_rest_positions = [(0, 0)] * self.au_list_size
		self.AU_deltas = [(0, 0)] * self.au_list_size

		self.anchor_input_indices = [0] * self.num_anchors
		self.anchor_AU_rest_positions = [(0, 0)] * self.num_anchors
		self.anchor_AU_deltas = [(0, 0)] * self.num_anchors

		self.rotation_list = [0, 0, 0] # x,y,z the units are arbitrary
		self.create_FACS_dictionary(au_file)

	def reset_runtime_structures(self):
		self.input_indices = [0] * self.au_list_size
		self.AU_rest_positions = [(0, 0)] * self.au_list_size
		self.AU_deltas = [(0, 0)] * self.au_list_size

		self.anchor_input_indices = [0] * self.num_anchors
		self.anchor_AU_rest_positions = [(0, 0)] * self.num_anchors
		self.anchor_AU_deltas = [(0, 0)] * self.num_anchors

	def get_input_frame(self):
		self.capture_object.set_image()
		self.capture_object.set_face()
		if self.capture_object.is_ready and self.capture_object.bbox:
			self.capture_object.set_landmarks()
			self.frame_number += 1
			return True
		return False

	def create_FACS_dictionary(self, facs_file):
		FACS_map = {}
		for i in range(29):
			FACS_map[i] = {"val_int": [0, 0], "val_float_in": [0.0, 0.0], "val_float_out": [0.0, 0.0],
										 "name": "", "au": i,
										 "AU_lmarks": {"left": [], "right": []},
										 "IN_lmarks": {"left": [], "right": []}, # named landmarks based on current implementation
										 "Blendshape":{"name": "","left": []}} # named blendshape based on current implementation

		f = open(facs_file, "r")
		i = 0
		for line in f:
			line = line.strip()
			if line == "|-":
				continue
			line = line.split('|')
			FACS_map[int(line[1])]["name"] = line[3]

		FACS_map['anchors'] = {"bottom": {"au": 0, "in": 0},
													 "mid": {"au": 0, "in": 0},
													 "top": {"au": 0, "in": 0},
													 "mouth": {"au": 0, "in": 0}}
		self.mapping = FACS_map

	def create_map_geometry(self):
		# data from https://en.wikipedia.org/wiki/Human_head
		bbox = self.capture_object.bbox
		fmap = self.mapping
		# take average of men and women
		lmarks = [[0, 0]] * len(fmap) * 2
		anchors = [[0, 0]] * 4  # bottom, mid, top, mouth
		AVERAGE_HEAD_HEIGHT = 18.4  # CENTI METERS
		AVERAGE_HEAD_WIDTH = 13.9  # CENTI METERS
		AVERAGE_HEAD_HEIGHT_INV = 1 / AVERAGE_HEAD_HEIGHT
		AVERAGE_HEAD_WIDTH_INV = 1 / AVERAGE_HEAD_WIDTH

		# first we need to get the marks closest to the bottom, mid and top to determine tilt of face
		# remember we are working in a bbox of the face so this is simply center bottom mid and top.
		# Nevermind, this is way harder than i expected it to be. So lets require "calibration" pose.
		# Assume face is in a vertical aligned position in order to extract and place initial FACS lmarks
		# and then use deltas from this position to determine rotations.

		if '_dlib_pybind11' in sys.modules:
			if bbox.__class__ == dlib.rectangle().__class__:
				# from bottom of bbox get span of lmarks below mid chin (human 1.5875)
				# temp_bottom_lmarks = sorted([x for x in input_lmarks if x[1] > bbox.bottom() - (bbox.height() * (1.5875 / AVERAGE_HEAD_HEIGHT))], key=lambda x:x[0])
				# bottom_span = temp_bottom_lmarks[-1][0] - temp_bottom_lmarks[0][0] if len(temp_bottom_lmarks) > 0 else bbox.width()//2
				anchors[0] = [bbox.left() + bbox.width() // 2, int(bbox.bottom() - (bbox.height() * (1.5 / AVERAGE_HEAD_HEIGHT)))]
				# get lmarks near mid of face heigth (human 9.2075)
				# top_mid_range = bbox.bottom() - (bbox.height() * (10.2075 / AVERAGE_HEAD_HEIGHT))
				# bottom_mid_range = bbox.bottom() - (bbox.height() * (8.2075 / AVERAGE_HEAD_HEIGHT))
				# temp_mid_lmarks = sorted([x for x in input_lmarks if (top_mid_range < x[1] < bottom_mid_range)], key=lambda x:x[0])
				anchors[1] = [bbox.left() + bbox.width() // 2,
											int(bbox.bottom() - (bbox.height() * (9.2075 / AVERAGE_HEAD_HEIGHT)))]
				# The top position can vary a lot. some lmarks give top of eybrow, some may give top of hairline
				# for starters assume top of hairline (since the test lmark uses this)
				# this is weird the openface bounding box is in forehead, but allows lmarks outside that range? odd
				anchors[2] = [bbox.left() + bbox.width() // 2,
											int(bbox.bottom() - (bbox.height() * (17.415 / AVERAGE_HEAD_HEIGHT)))]
				# anchors[2] = [bbox.left() + bbox.width()//2, bbox.top()]
				anchors[3] = [get_pixel(0, bbox, 0, 5.2), get_pixel(1, bbox, 0, .45)]

				# print("Width:", bbox.width())  # human 13.9
				# print("Height:", bbox.height())  # human 18.4
				# AU1 inner brow raiser: 25% of pupil to pupil 6.25/4 , 50% hairline - top of nose (18.4 - 11.7)/2
				lmarks[1] = [(bbox.left() + bbox.width() // 2) - int((bbox.width() * ((6.24 / 4) / AVERAGE_HEAD_WIDTH))),
										 bbox.bottom() - int(bbox.height() * (
													 (11.7 + ((AVERAGE_HEAD_HEIGHT - 11.7) * .5)) / AVERAGE_HEAD_HEIGHT))]  # left inner brow pixel
				lmarks[2] = [(bbox.left() + bbox.width() // 2) + int((bbox.width() * ((6.24 / 4) / AVERAGE_HEAD_WIDTH))),
										 bbox.bottom() - int(bbox.height() * (
													 (11.7 + ((AVERAGE_HEAD_HEIGHT - 11.7) * .5)) / AVERAGE_HEAD_HEIGHT))]  # right inner brow pixel

				# AU2 outer brow raiser: 25% of pupil to pupil 6.25/4 , 50% hairline - top of nose (18.4 - 11.7)/2
				lmarks[3] = [(bbox.left() + bbox.width() // 2) - int((bbox.width() * ((3 * 6.24 / 4) / AVERAGE_HEAD_WIDTH))),
										 bbox.bottom() - int(bbox.height() * (
													 (11.7 + ((AVERAGE_HEAD_HEIGHT - 11.7) * .5)) / AVERAGE_HEAD_HEIGHT))]  # left outer brow pixel
				lmarks[4] = [(bbox.left() + bbox.width() // 2) + int((bbox.width() * ((3 * 6.24 / 4) / AVERAGE_HEAD_WIDTH))),
										 bbox.bottom() - int(bbox.height() * (
													 (11.7 + ((AVERAGE_HEAD_HEIGHT - 11.7) * .5)) / AVERAGE_HEAD_HEIGHT))]  # right outer brow pixel

				# AU4 brow lower: 25% of pupil to pupil 6.25/4 , 50% hairline - top of nose (18.4 - 11.7) * .75
				lmarks[7] = [(bbox.left() + bbox.width() // 2) - int((bbox.width() * ((6.24 / 4) / AVERAGE_HEAD_WIDTH))),
										 bbox.bottom() - int(bbox.height() * (
													 (11.7 + ((AVERAGE_HEAD_HEIGHT - 11.7) * .75)) / AVERAGE_HEAD_HEIGHT))]  # left outer brow pixel
				lmarks[8] = [(bbox.left() + bbox.width() // 2) + int((bbox.width() * ((6.24 / 4) / AVERAGE_HEAD_WIDTH))),
										 bbox.bottom() - int(bbox.height() * ((11.7 + (
													 (AVERAGE_HEAD_HEIGHT - 11.7) * .75)) / AVERAGE_HEAD_HEIGHT))]  # right outer brow pixel

				# AU5 lid raise: center of pupil , at sellion
				lmarks[9] = [get_pixel(0, bbox, .05, (6.24 * .5)), get_pixel(1, bbox, .25, (11.7 * .75))]
				lmarks[10] = [get_pixel(2, bbox, .05, (6.24 * .5)), get_pixel(1, bbox, .25, (11.7 * .75))]

				# AU6 cheek raiser: (half out eye to outer eye), below eye
				lmarks[11] = [get_pixel(0, bbox, .05, (10.9 * .425)), get_pixel(1, bbox, 0, (11.7 * .85))]
				lmarks[12] = [get_pixel(2, bbox, .05, (10.9 * .425)), get_pixel(1, bbox, 0, (11.7 * .85))]

				# AU7 lid tightner: center of pupil , below pupil
				lmarks[13] = [get_pixel(0, bbox, .05, (6.24 * .75)), get_pixel(1, bbox, .25, (11.7 * .7))]
				lmarks[14] = [get_pixel(2, bbox, .05, (6.24 * .75)), get_pixel(1, bbox, .25, (11.7 * .7))]
				# AU8 lips toward each other
				# """SPECIAL CASE USE MOUTH ANCHOR"""

				# AU9 nose wrinkley:x, 14 - 16 - 9 //2
				lmarks[17] = [get_pixel(0, bbox, .05, (6.24 * .25)), get_pixel(1, bbox, 0, (9.375 * 1.25))]
				lmarks[18] = [get_pixel(2, bbox, .05, (6.24 * .25)), get_pixel(1, bbox, 0, (9.375 * 1.25))]

				# AU10 upper lip raise
				lmarks[19] = [get_pixel(0, bbox, 0, (6.24 * .325)), get_pixel(1, bbox, 0, (9.375 * 1))]
				lmarks[20] = [get_pixel(2, bbox, 0, (6.24 * .325)), get_pixel(1, bbox, 0, (9.375 * 1))]
				# AU11 nasolabial furrow deepener
				# """SPECIAL CASE USE 10 and 12, but small expression only"""

				# AU12 lip corner puller : x, 14-10
				lmarks[23] = [get_pixel(0, bbox, 0, (5.2 * .65)), get_pixel(1, bbox, 0, (4.45 * 1.25))]
				lmarks[24] = [get_pixel(2, bbox, 0, (5.2 * .65)), get_pixel(1, bbox, 0, (4.45 * 1.25))]
				# AU13 sharp lip puller
				lmarks[25] = [get_pixel(0, bbox, 0, (5.2 * .35)), get_pixel(1, bbox, 0, (4.45 * 1.45))]
				lmarks[26] = [get_pixel(2, bbox, 0, (5.2 * .35)), get_pixel(1, bbox, 0, (4.45 * 1.45))]
				# AU14 dimpler (buccantor)
				lmarks[27] = [get_pixel(0, bbox, 0, (5.2 * .5)), get_pixel(1, bbox, 0, (4.45 * 1.))]
				lmarks[28] = [get_pixel(2, bbox, 0, (5.2 * .5)), get_pixel(1, bbox, 0, (4.45 * 1.))]
				# AU15 lip corner deppressor
				lmarks[29] = [get_pixel(0, bbox, 0, (5.2 * .65)), get_pixel(1, bbox, 0, (4.45 * 1.))]
				lmarks[30] = [get_pixel(2, bbox, 0, (5.2 * .65)), get_pixel(1, bbox, 0, (4.45 * 1.))]
				# AU16 lower lip depressor
				lmarks[31] = [get_pixel(0, bbox, 0, (5.2 * .35)), get_pixel(1, bbox, 0, (4.45 * .75))]
				lmarks[32] = [get_pixel(2, bbox, 0, (5.2 * .35)), get_pixel(1, bbox, 0, (4.45 * .75))]
				# AU17 chin raiser
				# """SPECIAL CASE USE BOTTOM ANCHOR"""

				# AU18 lip pucker
				lmarks[35] = [get_pixel(0, bbox, 0, (5.2 * .225)), get_pixel(1, bbox, 0, (4.45 * 1.))]
				lmarks[36] = [get_pixel(2, bbox, 0, (5.2 * .225)), get_pixel(1, bbox, 0, (4.45 * 1.))]
				# AU19 lip corner deppressor
				# AU20 lip stretcher
				lmarks[39] = [get_pixel(0, bbox, 0, (5.2 * .65)), get_pixel(1, bbox, 0, (4.45 * .75))]
				lmarks[40] = [get_pixel(2, bbox, 0, (5.2 * .65)), get_pixel(1, bbox, 0, (4.45 * .75))]
				# AU22 lip funneler
				# """SPECIAL CASE USE 8,17,18, ANCHOR"""
				# AU23 lip tightener
				# """SPECIAL CASE USE MOUTH ANCHOR"""
				lmarks[45] = anchors[0]
				lmarks[46] = lmarks[45]
				# AU24 lip presser
				# """SPECIAL CASE USE negative 16, and positive 10 ANCHOR"""
				# AU26 and AU27 plus bottom anchor
				lmarks[51] = [get_pixel(0, bbox, .1, (5.2 * .75)), get_pixel(1, bbox, 0, (4.45 * 1.125))]
				lmarks[52] = [get_pixel(2, bbox, .1, (5.2 * .75)), get_pixel(1, bbox, 0, (4.45 * 1.125))]
				lmarks[53] = lmarks[51]
				lmarks[54] = lmarks[52]
			# AU28 ADVANCE MOVE MAYBE LATER
			for i in range(len(lmarks) // 2 - 2):
				fmap[i + 1]["AU_lmarks"]["left"].append(lmarks[2 * (i + 1) - 1])  # left lmark
				fmap[i + 1]["AU_lmarks"]["right"].append(lmarks[2 * (i + 1)])  # right lmark

			for i,k in enumerate(fmap['anchors']):
				fmap['anchors'][k]['au'] = anchors[i]
		return 0, anchors

	def init_map_input(self):
		fmap = self.mapping
		lmarks = self.capture_object.capture_data

		for k in fmap['anchors']:
			fmap['anchors'][k]["in"] = get_closest(lmarks, [fmap['anchors'][k]["au"]])

		for v in fmap:
			if v == 0 or v == 'anchors':
				continue
			else:
				fmap[v]["IN_lmarks"]["left"] = get_closest(lmarks, fmap[v]["AU_lmarks"]["left"])
				fmap[v]["IN_lmarks"]["right"] = get_closest(lmarks, fmap[v]["AU_lmarks"]["right"])

		self.reset_runtime_structures()

	def init_map_output(self):
		# bshapes is list of (au, [bshape_L],[bshape_R])
		for v in self.control_object.controls_data:
			if v[1][0] == -1:
				continue
			print(v)
			self.mapping[v[1][0] // 2]["Blendshape"]["left"] = v[1]
			self.mapping[v[1][0] // 2]["Blendshape"]["right"] = v[2]

	def calibrate_mapping(self):
		side = ["left", "right"]
		lmarks = self.capture_object.capture_data
		bbox = self.capture_object.bbox
		self.input_indices = [self.mapping[i // 2 + 1]["IN_lmarks"][side[i % 2]] for i in range(1, 56)]
		self.AU_rest_positions = [
			(((lmarks[x][0] - bbox.left()) / bbox.width() + (y[0] * (self.frame_number - 1))) / self.frame_number,
			((bbox.bottom() - lmarks[x][1]) / bbox.height() + (y[1] * (self.frame_number - 1))) / self.frame_number) for x, y in
			zip(self.input_indices, self.AU_rest_positions)]

		# bottom mid top mouth
		self.anchor_input_indices = [self.mapping['anchors'][i]["in"] for i in self.mapping['anchors']]
		self.anchor_AU_rest_positions = [
			(((lmarks[x][0] - bbox.left()) / bbox.width() + (y[0] * (self.frame_number - 1))) / self.frame_number,
			((bbox.bottom() - lmarks[x][1]) / bbox.height() + (y[1] * (self.frame_number - 1))) / self.frame_number) for
			x, y in zip(self.anchor_input_indices, self.anchor_AU_rest_positions)]

	def calculate_deltas(self):
		self.AU_deltas = do_delta_calc(self.capture_object.capture_data, self.capture_object.bbox,
																	self.input_indices, self.AU_rest_positions)
		self.anchor_AU_deltas = do_delta_calc(self.capture_object.capture_data, self.capture_object.bbox,
																				self.anchor_input_indices, self.anchor_AU_rest_positions)

	def calculate_rotations(self):
		# X-rot Look up/down

		tilt_A = self.anchor_AU_deltas[1][1] - self.anchor_AU_deltas[0][1]
		tilt_B = self.anchor_AU_deltas[2][1] - self.anchor_AU_deltas[1][1]
		self.rotation_list[0] = tilt_A if tilt_A > tilt_B else -tilt_B

		# Y-rot Look left/right
		self.rotation_list[1] = self.anchor_AU_deltas[1][0]


		'''
		TILT_SHIFT = 0
		if tilt_A > .02:
			window_one[2] += "up"
		elif tilt_B > .02:
			TILT_SHIFT = tilt_B
			window_one[2] += "down"
		else:
			window_one[2] += "no tilt"
		'''
		# Z-rot Tilt left/right

		self.rotation_list[2] = \
			np.arcsin(abs(self.anchor_AU_deltas[0][0] - self.rotation_list[1]) /
								(self.anchor_AU_rest_positions[1][1] - self.anchor_AU_rest_positions[0][1]))

	def extract_controls(self):

		for i, v in enumerate(self.control_object.controls_data):
				if v[1][0] != -1:
					ts = 0
					for t in v[1]:
						#todo prolly can use squared distance and drop the root. but require some changes to the rest of the logic
						delta_val = ((self.AU_deltas[t[0]][0]**2 + self.AU_deltas[t[0]][1]**2)**.5 - .01) / .08
						if delta_val < 0: # if any expression too low the blendshape is set to 0
							ts = 0
							break
						elif delta_val > 1:
							ts += t[1]  # clamp the value so blendshapes stay in "normal" range.
						else:
							ts += delta_val * t[1]
					#todo change this to just send values, let control class sort where in structure it goes
					self.control_object.controls_data[i][2] = ts/len(v[1])


########################################################################################################################
# Functions below are for called are used to do some MATH in the mapping class
########################################################################################################################
def do_delta_calc(lmarks, bbox,  index_list, rest_list):
	t = [((lmarks[x][0] - bbox.left()) / bbox.width(),
				(bbox.bottom() - lmarks[x][1]) / bbox.height()) for x in index_list]
	t = [(x[0] - y[0], x[1] - y[1]) for x, y in zip(t, rest_list)]
	# remove turn and tilt from each landmark
	# t_list = [(x[0] - TURN_SHIFT, x[1] - TILT_SHIFT) for x in AU_LIST_DELTAS]
	# remove the average that all the lmarks moved this should take out the the turn and tilt values
	t_avg = [(sum(tup) / len(t)) for tup in zip(*t)]
	# this should remove the tilt value out of each anchor, but something is not right.
	# t_list = [(x[0] - (np.sin(anchor_z_rot_theta)*y), x[1] - (np.cos(anchor_z_rot_theta)*y)) for x,y in zip(t_list, AU_LIST_DIS_TO_MID)]
	return [(x[0] - t_avg[0], x[1] - t_avg[1]) for x in t]

# mode: height == 1 width == 0 negate_height == 3 negate_width = 2
def get_pixel(mode, bbox, max_coef, cm):
	offset = bbox.bottom() if mode & 1 else bbox.left() + bbox.width() // 2
	pix_max = bbox.height() if mode & 1 else bbox.width()
	max_cm = 18.4 if mode & 1 else 14.8

	reverse = -1 if mode & 2 else 1
	return offset - (reverse * int(pix_max * ((max_coef - .05) + (cm / max_cm))))

def get_distance(a,b):
	return ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** .5

def get_closest(lmarks, side):
	au_l = (side[0][0], side[0][1])
	min_dis = float('inf')
	min_mark = 0
	for i, l in enumerate(lmarks):
		tmp = get_distance(au_l, l)
		if tmp < min_dis:
			min_dis = tmp
			min_mark = i
	return min_mark





