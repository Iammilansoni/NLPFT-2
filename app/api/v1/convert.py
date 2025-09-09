# Initialize components
rule_engine = RuleEngine()
assembler = Assembler()

@router.post("/convert", response_model=ConvertResponse)
async def convert(request: ConvertRequest):
    """
    Convert natural language instructions into structured test steps.
    """

    logger.info(f"Received text: {request.text}")

    # Step 1: Rule Engine Parsing
    steps = rule_engine.parse(request.text)
    logger.debug(f"Rule Engine Output: {steps}")

    # (Step 2: later add Semantic Matcher + Ranker)

    # Step 3: Assemble Final JSON
    result = assembler.assemble(steps)
    logger.info(f"Conversion completed: {result}")

    return result