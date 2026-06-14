import ee

try:
    ee.Initialize(project='disastemind')
    print("Earth Engine successfully initialized with project 'disastemind'!")
except Exception as e:
    print("Earth Engine initialization failed:")
    print(e)
