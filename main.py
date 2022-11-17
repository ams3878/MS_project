import cv2
import helpers
import camera
import mocap
import blendshapes
import time
from FACS import *
from tkinter import *
import numpy as np

specs, cam, vid_writer = camera.camera_setup()
#TODO change mocap dict to a mocap object with requiste functions
mocap_dict = mocap.mocap_setup(specs)


AU_LIST_SIZE = 29*2
NUM_ANCHORS = 4

AU_LIST_IN = [0] * AU_LIST_SIZE
AU_LIST_OFFSETS = [(0, 0)] * AU_LIST_SIZE
AU_LIST_DELTAS = [(0,0)] * AU_LIST_SIZE

AU_LIST_ANCHORS_OFFSETS = [(0,0)] * NUM_ANCHORS
AU_LIST_ANCHORS_DELTAS = [(0,0)] * NUM_ANCHORS
AU_LIST_ANCHORS = [0] * NUM_ANCHORS

AU_LIST_DIS_TO_BOTTOM = [0] * AU_LIST_SIZE

AU_FILE = open("au.txt", "w")
BS_FILE = open("bs.txt", "w")
DONE = False
print("Initializing MoCap...", end="")
while(not DONE):
	result, image = cam.read()
	mocap.find_face(image, mocap_dict)
	if result:
		if mocap_dict["bbox"] is not None:
			lmarks, bbox = mocap.get_lmarks(image, mocap_dict)
			FACS_map = create_FACS_dictionary("FACS_aus", {})
			# get facs: if calibration fails will return tuple, (0, error)
			create_FACS_Landmarks(bbox, lmarks, FACS_map)
			DONE = True
print("FINISHED.")
FRAME = -1
IS_WINDOW = False
txtarea = 0
window = 0
GO = True
CALIBRATE = 0
WAIT = False
def stop():
	global GO
	GO = False
def cal():
	global CALIBRATE, AU_LIST_ANCHORS_OFFSETS, AU_LIST_OFFSETS
	CALIBRATE = 0
	AU_LIST_ANCHORS_OFFSETS = [(0, 0)] * NUM_ANCHORS
	AU_LIST_OFFSETS = [(0, 0)] * AU_LIST_SIZE
def pause():
	global WAIT
	WAIT = False if WAIT else True

def start_window(t):
	# declare the window
	w = Tk()
	# set window title
	w.title(t)
	# set window width and height
	w.configure(width=1000, height=500)
	# set window background color
	w.configure(bg='lightgray')
	ta = Text(w, width=100, height=50)
	ta.pack(pady=20)
	b1 = Button(w, text="Delete", command=stop)
	b1.pack(pady=10)
	b2 = Button(w, text="Calibrate", command=cal)
	b2.pack(pady=10)
	b3 = Button(w, text="Pause", command=pause)
	b3.pack(pady=10)
	return True, ta, w

last_frame_time = 0
IS_WINDOW, txtarea, window = start_window("AUs")
IS_WINDOW2, txtarea2, window2 = start_window("BLENDSHAPEs")
BLENDSHAPES = blendshapes.get_bshapes()
while(GO):
	FRAME+=1
	wrtstr = ""
	#key = cv2.waitKey(1) & 0xFF

	result, image = cam.read()
	mocap.find_face(image, mocap_dict)

	if result:
		if mocap_dict["bbox"] is not None:  #todo move to get_lmarks
			lmarks, bbox = mocap.get_lmarks(image, mocap_dict)
			if True:
				CALIBRATE += 1
				side = ["left", "right"]
				if CALIBRATE == 1:
					map_LANDMARKS_to_FACS(lmarks, FACS_map)
					map_BLENDSHAPES_to_FACS([(1,[0,1],[0,2])], FACS_map)
				#set box size for funs

				AU_LIST_IN = [FACS_map[i // 2 + 1]["IN_lmarks"][side[i % 2]] for i in range(1, 56)]
				AU_LIST_OFFSETS = [(((lmarks[x][0] - bbox.left()) / bbox.width() + (y[0] * (CALIBRATE - 1))) / CALIBRATE,
												 ((bbox.bottom() - lmarks[x][1]) / bbox.height() + (y[1] * (CALIBRATE - 1))) / CALIBRATE) for x, y in zip(AU_LIST_IN, AU_LIST_OFFSETS)]

				#bottom mid top mouth
				AU_LIST_ANCHORS = [FACS_map['anchors'][i]["in"] for i in FACS_map['anchors']]
				AU_LIST_ANCHORS_OFFSETS = [(((lmarks[x][0] - bbox.left()) / bbox.width() + (y[0] * (CALIBRATE - 1))) / CALIBRATE,
														((bbox.bottom() - lmarks[x][1]) / bbox.height() + (y[1] * (CALIBRATE - 1))) / CALIBRATE) for
													 x, y in zip(AU_LIST_ANCHORS, AU_LIST_ANCHORS_OFFSETS)]

				#Initial distance from node to bottom anchor
				AU_LIST_DIS_TO_MID = [((x[0] - AU_LIST_ANCHORS_OFFSETS[1][0])**2 + (x[1] - AU_LIST_ANCHORS_OFFSETS[1][1])**2)**.5 for x in AU_LIST_OFFSETS]

			t_curs = [((lmarks[x][0] - bbox.left()) / bbox.width(),
														(bbox.bottom() - lmarks[x][1]) / bbox.height()) for x in AU_LIST_IN]
			AU_LIST_DELTAS = [(x[0] - y[0], x[1] - y[1]) for x,y in zip(t_curs, AU_LIST_OFFSETS)]

			t_curs_offset = [((lmarks[x][0] - bbox.left()) / bbox.width(),
																	(bbox.bottom() - lmarks[x][1]) / bbox.height()) for x in AU_LIST_ANCHORS]
			AU_LIST_ANCHORS_DELTAS = [(x[0] - y[0], x[1] - y[1]) for x,y in zip(t_curs_offset, AU_LIST_ANCHORS_OFFSETS)]

			# TURN CHECK
			AU_FILE.write("\nhead Y-rot: ")
			wrtstr += "\nhead Y-rot:"
			TURN_SHIFT = AU_LIST_ANCHORS_DELTAS[1][0]
			if .01 > AU_LIST_ANCHORS_DELTAS[1][0] > -.01:
				AU_FILE.write("No Turn")
				wrtstr += "No Turn"
				pass
			elif AU_LIST_ANCHORS_DELTAS[1][0] < 0:
				AU_FILE.write("Right")
				wrtstr += "Right"
				pass
			elif AU_LIST_ANCHORS_DELTAS[1][0] > 0:
				AU_FILE.write("LEFT")
				wrtstr += "LEFT"
				pass
			else:
				AU_FILE.write("err")
				wrtstr += "err"
				pass

			# TILT CHECK x-axis
			TILT_SHIFT = 0
			wrtstr += "\nhead X-ROT: "
			AU_FILE.write("\nhead X-ROT: ")
			if (AU_LIST_ANCHORS_DELTAS[1][1] - AU_LIST_ANCHORS_DELTAS[0][1]) > .02:
				TILT_SHIFT = AU_LIST_ANCHORS_DELTAS[1][1] - AU_LIST_ANCHORS_DELTAS[0][1]
				AU_FILE.write("up")
				wrtstr += "up"
			elif (AU_LIST_ANCHORS_DELTAS[2][1] - AU_LIST_ANCHORS_DELTAS[1][1]) > .02:
				TILT_SHIFT = AU_LIST_ANCHORS_DELTAS[2][1] - AU_LIST_ANCHORS_DELTAS[1][1]
				AU_FILE.write("down")
				wrtstr += "down"
			else:
				AU_FILE.write("err")
				wrtstr += "no tilt"


			# TILT CHECK y-axis
			anchor_z_rot_theta = np.arcsin((AU_LIST_ANCHORS_DELTAS[0][0] - TURN_SHIFT) / (AU_LIST_ANCHORS_OFFSETS[0][1] - AU_LIST_ANCHORS_OFFSETS[1][1] + .0000000001))
			AU_FILE.write("\nhead Z-rot: ")
			wrtstr += f"\nhead Z-rot: {(anchor_z_rot_theta / np.pi * 180):.2f}\t"
			if abs(anchor_z_rot_theta) < .02:
				AU_FILE.write("no tilt")
				wrtstr += "no tilt"
				pass
			elif anchor_z_rot_theta > 0:
				AU_FILE.write("left\n")
				wrtstr += "left"
				pass
			elif anchor_z_rot_theta < 0:
				AU_FILE.write("right")
				wrtstr += "right"
				pass
			else:
				AU_FILE.write("err")
				wrtstr += "err"
				pass
			#remove turn and tilt from each landmark
			#t_list = [(x[0] - TURN_SHIFT, x[1] - TILT_SHIFT) for x in AU_LIST_DELTAS]
			t_avg = [(sum(tup)/ len(AU_LIST_DELTAS)) for tup in zip(*AU_LIST_DELTAS)]
			t_list = [(x[0] - t_avg[0], x[1] - t_avg[1]) for x in AU_LIST_DELTAS]
			#t_list = AU_LIST_DELTAS
			'''		min_dx = min(t_list)[0]
			min_dy = min(t_list)[1]
			t_list = [((x[0] - (min_dx + .000001)), (x[0] - (min_dy + .000001))) for x in t_list]
			max_dx = max(t_list)[0]
			max_dy = max(t_list)[1]'''

			t_list = [(x[0] - (np.sin(anchor_z_rot_theta)*y), x[1] - (np.cos(anchor_z_rot_theta)*y)) for x,y in zip(t_list, AU_LIST_DIS_TO_BOTTOM)]
			#t_list = [(x[0]**2 + x[1]**2)**.5 * max([(np.sign(a), abs(a)) for a in [x[0], x[1]]],key=lambda t:t[1])[0] for x in t_list]
			t_list = [(x[0]**2 + x[1]**2)**.5 for x in t_list]
			for i in range(len(AU_LIST_DELTAS)//2):
				#x_1 = f"\nAU_{i+1}:\t(L: {', '.join(format(f, '.3f') for f in t_list[i//2] )})"
				#x_2 =	f"\tR: ({', '.join(format(f, '.3f') for f in t_list[i//2 + 1] )})"
				x_1 = f"\nAU_{i+1}:\tL: {format(t_list[i//2],'.3f')}\tR: {format(t_list[i//2 + 1],'.3f')}"
				wrtstr += x_1
				AU_FILE.write(x_1)
				#wrtstr += x_2
				#AU_FILE.write(x_2)

			AU_FILE.write(f"\nFrame: {FRAME}\n\n")
			wrtstr += f"\nFrame: {FRAME}\n\n"
			AU_FILE.seek(0)

			#todo replace with send bshapes to render
			wrtstr2 = ""
			wrtstr_out = f"{FRAME} "
			for i,v in enumerate(BLENDSHAPES):
				if len(v[1]) > 0:
					ts = 0
					for t in v[1]:
						t_list[t] -= .01
						t_list[t] /= .08
						if t_list[t] < 0:
							ts = 0
							break
						elif t_list[t] > 1:
							ts += 1
						else:
							ts += t_list[t]

					wrtstr2 += f"{i}: {v[0]} \t {ts/len(v[1])}\n"
					wrtstr_out += f"{ts/len(v[1])} "
				else:
					wrtstr_out += f"{-1} "

			BS_FILE.write(wrtstr_out + "\n")

			au_marks_to_draw = [x for i,x in enumerate(lmarks) if i in AU_LIST_IN]
			helpers.draw_landmarks(au_marks_to_draw, image, "test")
			# helpers.draw_landmarks(facs_lmarks, image, (0,0,200))


		# crop image
		image = image[specs["crop_image"]["top_y"]:specs["frame_dim"]["height"] - specs["crop_image"]["bottom_y"],
						specs["crop_image"]["left_x"]:specs["frame_dim"]["width"] - specs["crop_image"]["right_x"]]
		#vid_writer.write(image)
		#if FRAME % 10 == 0:
		cv2.imshow("GeeksForGeeks", image)
		cv2.imwrite("GeeksForGeeks.png", image)
		txtarea.delete("1.0", "end")
		txtarea.insert(END, wrtstr)
		window.update()
		txtarea2.delete("1.0", "end")
		txtarea2.insert(END, wrtstr2)
		window2.update()
		print(1/(time.time() - last_frame_time))
		last_frame_time = time.time()
		while(WAIT):
			sleep(5)
			continue
	else:
		print("No image detected. Please! try again")
AU_FILE.close()