import helpers
from mocap import MoCap_openface
from controls import ARkitControls
from MappingClasses import *

DEBUG_MODE = True
debug_controls = [True]
SHOW_CAPTURE = True
# arg1: number of AU's implemented
# arg2: number of controls
# At this time it is untested if different values will work here w/o changes elsewhere.
# this is ATM just used to initialize empty memory
FACS_object = FACS(29, 4)
FACS_object.capture_object = MoCap_openface()
FACS_object.control_object = ARkitControls("bs.txt")


print("Initializing MoCap...", end="")
while True:
	if FACS_object.get_input_frame():
		FACS_object.create_map_geometry()
		FACS_object.init_map_input()
		#atm this is done directly when object is created.
		#FACS_object.init_map_output()
		break
print("FINISHED.")
if DEBUG_MODE:
	import time
	last_frame_time = 0
	#this is tkinter info form: [tkinter text area, tkinter window, string to write with]
	window_one = helpers.start_window("AUs", FACS_object, debug_controls)
	window_two = helpers.start_window("BLENDSHAPEs", FACS_object, debug_controls)

while(True):
	if debug_controls[0] and FACS_object.get_input_frame():
		FACS_object.frame_number += 1

		#  calculate rest positions
		FACS_object.calibrate_mapping()

		# calculate the position deltas and rotations

		FACS_object.calculate_deltas()

		FACS_object.calculate_rotations()

		# use control dictionary to determine Control value from mapped AU delta
		FACS_object.extract_controls()

		# send the controls using the control object
		FACS_object.control_object.send_controls(FACS_object.frame_number)

		if DEBUG_MODE:

			# Turn CHECK y-axis
			window_one[2] += "\nhead Y-rot:"
			if FACS_object.anchor_AU_deltas[1][0] < -.01:
				window_one[2] += "Right"
			elif FACS_object.anchor_AU_deltas[1][0] > .01:
				window_one[2] += "LEFT"
			else:
				window_one[2] += "No Turn"

			# TILT CHECK x-axis
			window_one[2] += "\nhead X-ROT: "
			if FACS_object.rotation_list[0] > .02:
				window_one[2] += "up"
			elif FACS_object.rotation_list[0] < -.02:
				window_one[2] += "down"
			else:
				window_one[2] += "no tilt"
			# TILT CHECK z-axis
			ROT_ANGLE = FACS_object.rotation_list[2]
			window_one[2] += f"\nhead Z-rot: {(ROT_ANGLE / np.pi * 180):.2f}\t"
			if abs(ROT_ANGLE) < .02:
				window_one[2] += "no tilt"
				pass
			elif ROT_ANGLE > 0:
				window_one[2] += "left"
				pass
			elif ROT_ANGLE < 0:
				window_one[2] += "right"
				pass
			else:
				window_one[2] += "err"
				pass

			for i in range(len(FACS_object.AU_deltas) // 2):
				x_1 = f"\nAU_{i + 1}:\tL: {format(get_distance(FACS_object.AU_deltas[i // 2],(0,0)), '.3f')}" \
							f"\tR: {format(get_distance(FACS_object.AU_deltas[i // 2 + 1],(0,0)), '.3f')}"
				window_one[2] += x_1

			window_one[2] += f"\nFrame: {FACS_object.frame_number}\n\n"

			for i, v in enumerate(FACS_object.control_object.controls_data):
				window_two[2] += f"{i}: {v[0]} \t {v[2]}\n"

			au_marks_to_draw = [x for i, x in enumerate(FACS_object.capture_object.capture_data) if i in FACS_object.input_indices]
			helpers.draw_landmarks(au_marks_to_draw, FACS_object.capture_object.current_image, "test")
			print(1 / (time.time() - last_frame_time + .00000001))

		if SHOW_CAPTURE:
			# crop image
			import camera
			#helpers.draw_landmarks([], FACS_object.capture_object.current_image, "test")

			image = FACS_object.capture_object.current_image
			specs = FACS_object.capture_object.capture_specs
			image = image[specs["crop_image"]["top_y"]:specs["frame_dim"]["height"] - specs["crop_image"]["bottom_y"],
							specs["crop_image"]["left_x"]:specs["frame_dim"]["width"] - specs["crop_image"]["right_x"]]

			camera.display_cam("test", image)
	if DEBUG_MODE:
		last_frame_time = time.time()
		helpers.update_window(window_one, debug_controls)
		helpers.update_window(window_two, debug_controls)
	else:
		print("No image detected. Please! try again")
