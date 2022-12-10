from tkinter import *

def draw_landmarks(landmarks, image, color=(0, 0, 0)):
	cnt = 0
	test_color = False
	if color == "test": test_color = True
	for i in landmarks:
		if test_color:
			if cnt < 20:
				color = (0, 0, 10*cnt)
			elif cnt < 40:
				color = (0, 200, 0)
			elif cnt < 60:
				color = (10*cnt, 0, 0)
			else:
				color = (10*cnt, 10*cnt, 0)

		if i[1] + 3 < len(image) and i[0] + 3 < len(image[0]):
			image[i[1]][i[0]] = color
			for w in range(3):
				for l in range(3):
					image[i[1] + w][i[0] + l] = color
					image[i[1] - w][i[0] - l] = color
					image[i[1] + w][i[0] - l] = color
					image[i[1] - w][i[0] + l] = color

		cnt += 1

def stop():
	global GO
	GO = False

def cal():
	global  FACS_object
	FACS_o = FACS_object  # workaround, find good way to pass obj
	FACS_o.anchor_AU_rest_positions = [(0, 0)] * FACS_o.num_anchors
	FACS_o.AU_rest_positions = [(0, 0)] * FACS_o.num_AUs

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
	return [ta, w, ""]

def update_window(w):
	w[0].delete("1.0", END)
	w[0].insert(END, w[2])
	w[2] = ""
	w[1].update()