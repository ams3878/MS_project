import openface
def mocap_setup(s):
	s["dlibs_path"] = "C:\\Users\\Aaron\\PycharmProjects\\MS_project\\shape_predictor_81_face_landmarks.dat"
	new_mocap_dict = {"align": openface.AlignDlib(s["dlibs_path"]), "bbox": None, "face": None}
	return new_mocap_dict

def find_face(image, mocap_dict):
	mocap_dict["bbox"] = mocap_dict["align"].getLargestFaceBoundingBox(image)
	mocap_dict["face"] = mocap_dict["align"].align(len(image), image, 	mocap_dict["bbox"], landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)
	return 0

def get_lmarks(image, mocap_dict):
	return mocap_dict["align"].findLandmarks(image, mocap_dict["bbox"]), mocap_dict["bbox"]
