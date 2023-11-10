-include .env

ifneq ("$(wildcard .env)","")
include Makefile.migrations
endif

include Makefile.ci
