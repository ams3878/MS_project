import openface
import camera

class MoCapBaseClass:
	def __init__(self):
		self.bbox = None
		self.face = None
		self.capture_data = None  # typically landmarks
		self.current_image = None
		self.capture_device_type = 0
		self.capture_device = None
		self.capture_specs = None

		self.is_ready = False
	######################################
	#  required functions: these will be called by mapping class
	######################################

	def set_image(self, image):
		pass

	def set_face(self):
		pass

	def get_landmarks(self):
		pass

	######################################
	#  optional functions: these are some functions to interact with the capture device
	#    and will never be called by the mapping class
	######################################

	def setup_capture_device(self):
		if self.capture_device_type == 0:
			self.capture_specs, self.capture_device = camera.camera_setup()

	def read_capture_device(self):
		return self.capture_device.read()

class MoCap_openface(MoCapBaseClass):
	def __init__(self, settings_dict=None):
		super().__init__()
		self.dlibs_path = "C:\\Users\\Aaron\\PycharmProjects\\MS_project\\shape_predictor_81_face_landmarks.dat"
		self.align_object = openface.AlignDlib(self.dlibs_path)
		self.setup_capture_device()

	def set_image(self, image=None):
		if image:
			self.is_ready = True
			self.current_image = image
		else:
			self.is_ready, self.current_image = self.read_capture_device()

	def set_face(self):
		self.bbox = self.align_object.getLargestFaceBoundingBox(self.current_image)
		self.face = self.align_object.align(len(self.current_image), self.current_image, self.bbox, landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)

	def set_landmarks(self):
		self.capture_data = self.align_object.findLandmarks(self.current_image, self.bbox)
