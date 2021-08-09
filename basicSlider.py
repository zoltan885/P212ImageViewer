from qtrangeslider import QRangeSlider
from qtrangeslider.qtcompat.QtCore import Qt
from qtrangeslider.qtcompat.QtWidgets import QApplication


def update(tup):
    print('Min: %d; Max: %d', (tup[0], tup[1]))

app = QApplication([])

slider = QRangeSlider(Qt.Horizontal)
slider.setMinimum(5)
slider.setMaximum(55)
slider.setValue((10, 12))

slider.valueChanged.connect(update)

slider.show()

app.exec_()
