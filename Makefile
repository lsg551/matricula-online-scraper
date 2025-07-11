VERSION_RAW = $(shell git describe --tags --abbrev=0 2> /dev/null || echo "0.0.0")
VERSION = $(shell echo $(VERSION_RAW) | sed 's/^v//')
COMMIT = $(shell git rev-parse --short HEAD)
DATE = $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')

# NOTE: if the image shouldn't be the "default" image, omit the `:latest` tag

build-container:
	podman build -f Containerfile \
	-t ghcr.io/lsg551/matricula-online-scraper:${VERSION} \
	-t ghcr.io/lsg551/matricula-online-scraper:latest \
	--label org.opencontainers.image.revision=${COMMIT} \
	--label org.opencontainers.image.version=${VERSION} \
	--label org.opencontainers.image.created=${DATE} \
	.

# NOTE: login first
# set your GitHub Personal Access Token (PAT) as an environment variable
# echo $CR_PAT | podman login ghcr.io -u <USER> --password-stdin

push-container:
	podman push ghcr.io/lsg551/matricula-online-scraper:${VERSION}
	podman push ghcr.io/lsg551/matricula-online-scraper:latest
