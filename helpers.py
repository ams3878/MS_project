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

