.PHONY: all bump-version push-no-tag

all: push-no-tag

VERSION_FILE=./classes/__init__.py
VERSION=$(shell python3 -c 'import re; f=open("$(VERSION_FILE)"); print(re.search(r"__version__ = \"(.*?)\"", f.read()).group(1))')

bump-version:
	@echo "Current version: $(VERSION)"
	@read -p "Choose version type to bump (major, minor, patch -> 'major.minor.patch'): " versiontype; \
	case $$versiontype in \
		patch) newversion=$$(echo $(VERSION) | awk -F. '{printf "%d.%d.%d", $$1, $$2, $$3+1}');; \
		minor) newversion=$$(echo $(VERSION) | awk -F. '{printf "%d.%d.%d", $$1, $$2+1, 0}');; \
		major) newversion=$$(echo $(VERSION) | awk -F. '{printf "%d.%d.%d", $$1+1, 0, 0}');; \
		*) echo "Invalid option! Please choose either major, minor, or patch."; exit 1;; \
	esac; \
	sed -i "s/__version__ = \"$(VERSION)\"/__version__ = \"$$newversion\"/" $(VERSION_FILE); \
	echo "Version updated to $$newversion"; \
	read -p "Enter commit message: " commitmsg; \
	git add .; \
	git commit -am "$$commitmsg (version $$newversion)"; \
	git tag -fa v$$newversion -m "$$commitmsg"; \
	git push --follow-tags

push-no-tag:
	read -p "Enter commit message: " commitmsg; \
	git add .; \
	git commit -am "$$commitmsg"; \
	git push