DOCKER_IMAGE_GEM5?=ghcr.io/gem5/ubuntu-22.04_all-dependencies:v25-0-$(USER)
DOCKER_IMAGE_GPUFS?=ghcr.io/gem5/gpu-fs:v25-0-$(USER)
DOCKER_IMAGE_GCNGPU?=ghcr.io/gem5/gcn-gpu:v25-0-$(USER)
DOCKER_FILE_GEM5?=Dockerfile-gem5
DOCKER_FILE_GPUFS?=Dockerfile-gpufs
DOCKER_FILE_GCNGPU?=Dockerfile-gcngpu
# For use with --no-cache, etc.
DOCKER_BUILD_OPT?=
# Reconstruct the timezone for tzdata
TZFULL=$(subst /, ,$(shell readlink /etc/localtime))
TZ=$(word $(shell expr $(words $(TZFULL)) - 1 ),$(TZFULL))/$(word $(words $(TZFULL)),$(TZFULL))


all: build-gem5

build-gem5:
	docker build --build-arg TZ_ARG=$(TZ) $(DOCKER_BUILD_OPT) -f $(DOCKER_FILE_GEM5) -t $(DOCKER_IMAGE_GEM5) .

build-gpufs:
	docker build --build-arg TZ_ARG=$(TZ) $(DOCKER_BUILD_OPT) -f $(DOCKER_FILE_GPUFS) -t $(DOCKER_IMAGE_GPUFS) .

build-gcngpu:
	docker build --build-arg TZ_ARG=$(TZ) $(DOCKER_BUILD_OPT) -f $(DOCKER_FILE_GCNGPU) -t $(DOCKER_IMAGE_GCNGPU) .


run: run-gem5

run-gem5:
	docker run --rm -it \
		--device /dev/kvm \
		--cap-add=CAP_PERFMON \
		-v "${HOME}/.cache:${HOME}/.cache" \
		-v "/home/share/HDstorage/${USER}:/home/share/HDstorage/${USER}" \
		--user $(shell id -u):$(shell id -g) \
		--group-add $(shell getent group kvm | cut -d: -f3) \
		--group-add $(shell getent group libvirt | cut -d: -f3) \
		-w "${PWD}/.." \
		-e GEM5_RESOURCE_DIR \
		-e HOME \
		$(DOCKER_IMAGE_GEM5)

run-gpufs:
	docker run --rm -it \
		-v "${HOME}/.cache:${HOME}/.cache" \
		-v "/home/share/HDstorage/${USER}:/home/share/HDstorage/${USER}" \
		--user $(shell id -u):$(shell id -g) \
		-w "${PWD}/../gem5-resources/src/gpu/square" \
		-e HOME \
		$(DOCKER_IMAGE_GPUFS)

run-gcngpu:
	docker run --rm -it \
		-v "${HOME}/.cache:${HOME}/.cache" \
		-v "/home/share/HDstorage/${USER}:/home/share/HDstorage/${USER}" \
		--user $(shell id -u):$(shell id -g) \
		-w "${PWD}/.." \
		-e GEM5_RESOURCE_DIR \
		-e HOME \
		$(DOCKER_IMAGE_GCNGPU)

.PHONY: all build-gem5 build-gpufs build-gcngpu run run-gem5 run-gpufs run-gcngpu
