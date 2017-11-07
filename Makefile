ROOT = $(shell git rev-parse --show-toplevel)


$(ROOT)/.docker/flake8: $(ROOT)/docker/flake8.Dockerfile
	docker build --tag flake8 --file docker/flake8.Dockerfile docker
	mkdir -p $(ROOT)/.docker
	touch $(ROOT)/.docker/flake8

$(ROOT)/.docker/tooling: $(ROOT)/docker/tooling.Dockerfile
	docker build --tag tooling --file docker/tooling.Dockerfile docker
	mkdir -p $(ROOT)/.docker
	touch $(ROOT)/.docker/tooling


lint: $(ROOT)/.docker/flake8
	docker run --rm --tty --volume $(ROOT):/src flake8

check-release-file:
	docker run --rm --tty \
		--volume $(ROOT):/src \
		--workdir /src \
		python:3-alpine scripts/check-release-file.py

deploy: $(ROOT)/.docker/tooling
	env > env.list
	docker run --rm --tty \
		--env-file env.list \
		--volume $(ROOT):/src \
		tooling scripts/deploy.py


.PHONY: lint check-release-file deploy
