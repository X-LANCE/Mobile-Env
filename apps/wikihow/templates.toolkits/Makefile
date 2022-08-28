#!/usr/bin/make -f

OUTPUT_DIR = ../templates.out
INSTANCE_DIR = ../templates.instances
TEMPLATE_DIR = ../templates

ifdef HUMAN
	zpp_macro = --def HUMAN
else
	zpp_macro =
endif

task_confs := $(wildcard $(INSTANCE_DIR)/*.task)
task_protos := $(addsuffix .textproto,$(basename $(task_confs)))

.PHONY: all clean
all: $(addprefix $(OUTPUT_DIR)/,$(notdir $(task_protos)))
clean:
	rm -f $(OUTPUT_DIR)/*.textproto

.ONESHELL:
$(OUTPUT_DIR)/%.textproto: $(INSTANCE_DIR)/%.task
	tempdir=$$(mktemp -d -p /tmp)
	echo $$tempdir
	class_list=$$(awk -F- '{class_array[$$1] = 1;} END{for(cl in class_array) print cl;}' $<)
	for cl in $$class_list; do \
		zpp -m C $(zpp_macro) $(TEMPLATE_DIR)/$$cl.textproto.template -o $$tempdir/$$cl.textproto.template; \
	done
	python parse.py --task $< -p $$tempdir -o $@
	rm -rf $$tempdir
