import openface
class MoCapBaseClass:
	def __init__(self):
		self.bbox = None
		self.face = None
		self.current_image = None

	def set_image(self, image):
		pass
	def set_face(self):
		pass
	def get_lmarks(self):
		pass

class MoCap_openface(MoCapBaseClass):
	def __init__(self, settings_dict):
		super().__init__()
		self.dlibs_path = "C:\\Users\\Aaron\\PycharmProjects\\MS_project\\shape_predictor_81_face_landmarks.dat"
		self.align_object = openface.AlignDlib(self.dlibs_path)

	def set_image(self, image):
		self.current_image = image

	def set_face(self):
		self.bbox = self.align_object.getLargestFaceBoundingBox(self.current_image)
		self.face = self.align_object.align(len(self.current_image), self.current_image, self.bbox, landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)

	def get_lmarks(self):
		return self.align_object.findLandmarks(self.current_image, self.bbox)

