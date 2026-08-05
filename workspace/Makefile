PYTHON = python3
REPORT = audit_report.txt

.PHONY: report clean

audit:
	$(PYTHON) audit_runner.py --fixtures fixtures/ --output $(REPORT)

report:
	@cat $(REPORT)

clean:
	rm -rf $(REPORT) fixtures/
