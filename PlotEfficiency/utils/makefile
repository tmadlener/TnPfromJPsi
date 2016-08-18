ROOT_CONFIG=$(shell root-config --libs --cflags)

CXX=g++
CXXFLAGS=-Wall

all: saveCanvas

saveCanvas: saveCanvas.C
	$(CXX) $^ $(ROOT_CONFIG) $(CXXFLAGS) -o $@
