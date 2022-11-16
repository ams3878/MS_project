import sys
import dlib
from time import sleep


# mode: height == 1 width == 0 negate_height == 3 negate_width = 2

def get_pixel(mode, bbox, max_coef, cm):
	offset = bbox.bottom() if mode & 1 else bbox.left() + bbox.width() // 2
	pix_max = bbox.height() if mode & 1 else bbox.width()
	max_cm = 18.4 if mode & 1 else 14.8

	reverse = -1 if mode & 2 else 1
	return offset - (reverse * int(pix_max * ((max_coef - .05) + (cm / max_cm))))


def create_FACS_dictionary(facs_file, FACS_map):
	if not FACS_map: FACS_map = {}
	for i in range(29):
		FACS_map[i] = {"val_int": [0, 0], "val_float_in": [0.0, 0.0], "val_float_out": [0.0, 0.0],
									 "name": "", "au": i,
									 "AU_lmarks": {"left": [], "right": []},
									 "IN_lmarks": {"left": [], "right": []},
									 "Blendshape":{"left": [], "right": []}}

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
	return FACS_map


def create_FACS_Landmarks(bbox, input_lmarks, fmap):
	# data from https://en.wikipedia.org/wiki/Human_head
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

def map_LANDMARKS_to_FACS(lmarks, fmap):
	for k in fmap['anchors']:
		fmap['anchors'][k]["in"] = get_closest(lmarks, [fmap['anchors'][k]["au"]])

	for v in fmap:
		if v == 0 or v == 'anchors':
			continue
		else:
			fmap[v]["IN_lmarks"]["left"] = get_closest(lmarks, fmap[v]["AU_lmarks"]["left"])
			fmap[v]["IN_lmarks"]["right"] = get_closest(lmarks, fmap[v]["AU_lmarks"]["right"])


def map_BLENDSHAPES_to_FACS(bshapes, fmap):
	# bshapes is list of (au, [bshape_L],[bshape_R])
	for v in bshapes:
		if v == 0 or v == 'anchors':
			continue
		else:
			fmap[v[0]]["Blendshape"]["left"] = v[1]
			fmap[v[0]]["Blendshape"]["right"] = v[2]
