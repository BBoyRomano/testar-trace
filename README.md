# TESTAR Requirements Traceability

Research repository accompanying the Master's thesis:

**Requirements Traceability for Scriptless GUI Testing**

This study develops and evaluates a method for tracing user stories to TESTAR-generated GUI State Models to assess user story execution completeness and enable requirements coverage analysis in scriptless GUI testing.

## Repository Structure

- [`docs/`](docs/) — Method documentation and experimental configurations
- [`data/`](data/) — User stories and exported GUI State Models (JSON)
- [`prototype/`](prototype/) — Research prototype implementation
- [`evaluation/`](evaluation/) — Reference set, metrics, and evaluation results
- [`papers/`](papers/) — Research documents (LaTeX)

## Reproducibility

The primary System Under Test (SUT) used in this study is Parabank (https://para.testar.org/).

GUI State Models were generated using TESTAR and exported to JSON using the built-in export functionality.

The configurations used for each experimental run are documented in [`docs/experiment-configs/`](docs/experiment-configs/), and the resulting exported GUI State Models are available in [`data/models/`](data/models/).

## Related Project

This study builds upon TESTAR, an open-source tool for scriptless GUI testing:

- Source code: https://github.com/TESTARtool
- Website: https://testar.org/

## Citation

If you use this repository or its artifacts, please cite the associated Master's thesis. See [`CITATION.cff`](CITATION.cff) for citation details.

## License

MIT License — see [LICENSE](LICENSE).
