#!/usr/bin/env python3
"""
CLI script to run the project-level transpilation workflow.
"""
import os
import argparse
import json
import time
from pathlib import Path
from loguru import logger

from core import (
    # State components
    ProjectState,
    FileState,
    StateError,
    # Project components
    clone_project_structure,
    analyze_dependencies,
    get_transpilation_order,
    identify_test_files,
    clone_test_files,
    generate_tests,
    # Execution components
    ParallelExecutionManager,
    SingleFileProcessor,
    # Optimization components
    ProjectOptimizer,
)

from dotenv import load_dotenv


def main():
    """Main entry point for project-level transpilation."""
    _ = load_dotenv()

    parser = argparse.ArgumentParser(description="Run project-level transpilation")
    parser.add_argument("--model-name", required=True, help="LLM model name")
    parser.add_argument(
        "--source-dir", required=True, help="Path to source project directory"
    )
    parser.add_argument(
        "--target-dir", required=True, help="Path to target project directory"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Number of parallel transpilation agents",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum transpilation retries on error",
    )
    parser.add_argument(
        "--skip-optimization", action="store_true", help="Skip the optimization phase"
    )
    parser.add_argument(
        "--skip-tests", action="store_true", help="Skip test cloning/generation"
    )
    parser.add_argument(
        "--report-file",
        default="transpilation_report.json",
        help="Path to save the transpilation report",
    )
    args = parser.parse_args()

    logger.info(f"Running Project-Level Transpile with {args.model_name} model")

    # Convert paths to Path objects
    source_dir = Path(args.source_dir)
    target_dir = Path(args.target_dir)

    # Validate source directory
    if not source_dir.exists() or not source_dir.is_dir():
        logger.error(
            f"Source directory {source_dir} does not exist or is not a directory"
        )
        return 1

    # Phase 1: Clone project structure
    logger.info("Phase 1: Cloning project structure")
    start_time = time.time()
    file_mapping = clone_project_structure(source_dir, target_dir)
    logger.info(f"Project structure cloned in {time.time() - start_time:.2f} seconds")

    if not file_mapping:
        logger.error("No Java files found in source directory")
        return 1

    # Phase 2: Analyze dependencies
    logger.info("Phase 2: Analyzing dependencies")
    start_time = time.time()
    dependencies = analyze_dependencies(source_dir)
    logger.info(f"Dependencies analyzed in {time.time() - start_time:.2f} seconds")

    # Get optimal transpilation order
    transpilation_order = get_transpilation_order(dependencies)
    logger.info(f"Transpilation order determined with {len(transpilation_order)} files")

    # Create file states
    file_states = {}
    for source_file, target_file in file_mapping.items():
        file_states[source_file] = FileState(
            code="",
            original_code="",  # Will be loaded during transpilation
            scratchpad="",
            last_error=StateError(status=0, message=""),
            current_iterations=0,
            relative_path=source_file.relative_to(source_dir),
            target_path=target_file,
            dependencies=[],  # Will be populated from dependencies
            transpilation_status="pending",
            optimization_status="pending",
            retry_count=0,
            error_reports=[],
        )

    # Create project state
    project_state = ProjectState(
        source_dir=source_dir,
        target_dir=target_dir,
        file_states=file_states,
        dependencies=dependencies,
        optimization_context={},
        current_phase="structure_clone",
        max_retries=args.max_retries,
        concurrency=args.concurrency,
        manual_review_files=[],
        model_name=args.model_name,
    )

    # Phase 3: Transpile files in parallel
    logger.info("Phase 3: Transpiling files in parallel")
    project_state.current_phase = "transpile"
    start_time = time.time()

    parallel_manager = ParallelExecutionManager(
        project_state=project_state, file_processor=SingleFileProcessor.process_file
    )
    parallel_manager.run()

    logger.info(f"Transpilation completed in {time.time() - start_time:.2f} seconds")

    # Report on transpilation results
    total_files = len(file_states)
    completed = sum(
        1 for state in file_states.values() if state.transpilation_status == "completed"
    )
    failed = sum(
        1 for state in file_states.values() if state.transpilation_status == "failed"
    )

    logger.info(
        f"Transpilation complete: {completed}/{total_files} files successful, {failed} failed"
    )

    if project_state.manual_review_files:
        logger.warning(
            f"{len(project_state.manual_review_files)} files need manual review"
        )

        # Save manual review report
        report_path = target_dir / "manual_review_report.json"
        with open(report_path, "w") as f:
            json.dump(project_state.manual_review_files, f, indent=2, default=str)

        logger.info(f"Manual review report saved to {report_path}")

    # Phase 4: Clone or generate tests
    if not args.skip_tests:
        logger.info("Phase 4: Handling tests")
        project_state.current_phase = "tests"
        start_time = time.time()

        # Identify test files
        test_files = identify_test_files(source_dir)

        if test_files:
            logger.info(f"Found {len(test_files)} test files, cloning...")

            # Import here to avoid circular imports
            from langchain_openai import ChatOpenAI
            from pydantic import SecretStr
            import os

            # Get API key with fallback
            api_key = os.getenv("OPEN_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPEN_API_KEY environment variable required. "
                    "Please set one of these in your .env file or environment."
                )

            # Initialize LLM client for test conversion
            model = ChatOpenAI(
                model=args.model_name,
                temperature=0.2,
                api_key=SecretStr(api_key),
                base_url=os.getenv("OPEN_BASE_URL", "https://api.openai.com/v1"),
            )

            # Clone test files
            test_mapping = clone_test_files(
                test_files=test_files,
                source_dir=source_dir,
                target_dir=target_dir,
                model=model,
            )

            logger.info(f"Cloned {len(test_mapping)} test files")
        else:
            logger.info("No test files found, generating tests...")

            # Get list of successfully transpiled files
            successful_source_files = []
            successful_target_files = []

            for source_file, file_state in file_states.items():
                if (
                    file_state.transpilation_status == "completed"
                    and file_state.target_path is not None
                ):
                    successful_source_files.append(source_file)
                    successful_target_files.append(file_state.target_path)

            # Import here to avoid circular imports
            from langchain_openai import ChatOpenAI
            from pydantic import SecretStr
            import os

            # Get API key with fallback
            api_key = os.getenv("OPEN_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPEN_API_KEY environment variable required. "
                    "Please set one of these in your .env file or environment."
                )

            # Initialize LLM client for test generation
            model = ChatOpenAI(
                model=args.model_name,
                temperature=0.2,
                api_key=SecretStr(api_key),
                base_url=os.getenv("OPEN_BASE_URL", "https://api.openai.com/v1"),
            )

            # Generate tests
            generated_tests = generate_tests(
                source_files=successful_source_files,
                target_files=successful_target_files,
                model=model,
            )

            logger.info(f"Generated {len(generated_tests)} test files")

        logger.info(
            f"Test handling completed in {time.time() - start_time:.2f} seconds"
        )

    # Phase 5: Optimize project (if not skipped)
    if not args.skip_optimization:
        logger.info("Phase 5: Optimizing project")
        project_state.current_phase = "optimize"
        start_time = time.time()

        # Get API key for optimization
        import os  # Ensure os module is available

        api_key = os.getenv("OPEN_API_KEY")
        if not api_key:
            raise ValueError(
                "OPEN_API_KEY environment variable required for optimization"
            )

        base_url = os.getenv("OPEN_BASE_URL", "https://api.openai.com/v1")
        optimizer = ProjectOptimizer(
            project_state, args.model_name, api_key=api_key, base_url=base_url
        )
        optimization_results = optimizer.optimize()

        # Save optimization report
        optimization_report_path = target_dir / "optimization_report.json"
        with open(optimization_report_path, "w") as f:
            json.dump(optimization_results, f, indent=2, default=str)

        logger.info(f"Optimization completed in {time.time() - start_time:.2f} seconds")
        logger.info(f"Optimization report saved to {optimization_report_path}")

    # Save overall transpilation report
    report = {
        "source_dir": str(source_dir),
        "target_dir": str(target_dir),
        "total_files": total_files,
        "completed_files": completed,
        "failed_files": failed,
        "manual_review_files": len(project_state.manual_review_files),
        "file_statuses": {
            str(source_file): {
                "target_file": str(file_state.target_path),
                "status": file_state.transpilation_status,
                "retry_count": file_state.retry_count,
            }
            for source_file, file_state in file_states.items()
        },
    }

    report_path = target_dir / args.report_file
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Project transpilation complete. Output in {target_dir}")
    logger.info(f"Transpilation report saved to {report_path}")

    return 0


if __name__ == "__main__":
    exit(main())
