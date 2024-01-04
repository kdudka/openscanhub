# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
import sys

from osh.worker.csmock_runner import CsmockRunner
from osh.worker.tasks.task_build import OSHTaskBase


class AnalyzerVersionRetriever(OSHTaskBase):
    """
        Execute diff scan between two versions/releases of a package for
        Errata Tool
    """
    enabled = True

    def run(self):
        # string, comma separated list of analyzers
        analyzers = self.args.pop('analyzers')
        mock_config = self.args.pop('mock_config')
        su_user = self.args.pop('su_user', None)
        csmock_args = self.args.pop("csmock_args", None)

        with CsmockRunner() as runner:
            results, retcode = runner.no_scan(analyzers,
                                              profile=mock_config,
                                              su_user=su_user,
                                              additional_arguments=csmock_args)

            print('Retcode:', retcode)

            # upload results back to hub
            if results is None:
                print("Task did not produce any results", file=sys.stderr)
                self.fail()

            try:
                base_results = os.path.basename(results)
                with open(results, "rb") as f:
                    self.hub.upload_task_log(f, self.task_id, base_results)
            except OSError as e:
                print("Reading task logs failed:", e, file=sys.stderr)
                self.fail()

        if retcode > 0:
            print(f"Analyzer version retrieval has not completed successfully ({retcode})",
                  file=sys.stderr)
            self.fail()

        self.hub.worker.finish_analyzers_version_retrieval(self.task_id, base_results)
