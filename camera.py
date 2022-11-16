import cv2

def get_cv2_specs(cam, port):
	specs = {"cam_port": port}
	specs["frame_dim"] = {"width": int(cam.get(3)), "height": int(cam.get(4))}
	specs["crop_image"] = {"left_x": 100, "right_x": 100, "bottom_y": 0, "top_y": 100}
	specs["size"] = (specs["frame_dim"]["width"] - specs["crop_image"]["left_x"] - specs["crop_image"]["right_x"],
									 specs["frame_dim"]["height"] - specs["crop_image"]["bottom_y"] - specs["crop_image"]["top_y"])
	return specs

def get_camera(port):
	return cv2.VideoCapture(port)

def camera_setup():
	p = 0
	c = get_camera(p)
	s = get_cv2_specs(c, p)
	vw = cv2.VideoWriter('filename1.avi', cv2.VideoWriter_fourcc(*'MJPG'), 10, s["size"])
	return s, c, vw
