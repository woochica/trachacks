package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.jface.text.rules.MultiLineRule;
import org.eclipse.jface.text.rules.PatternRule;
import org.eclipse.jface.text.rules.RuleBasedPartitionScanner;
import org.eclipse.jface.text.rules.SingleLineRule;
import org.eclipse.jface.text.rules.Token;

public class WikiPartitionScanner extends RuleBasedPartitionScanner {

	public static final String SectionToken = "__section";

	public static final String SourceToken = "__source";

	public WikiPartitionScanner() {
		PatternRule[] rules = new PatternRule[7];

		rules[0] = new SingleLineRule("====== ", " ======\n", new Token(
				SectionToken));
		rules[1] = new SingleLineRule("===== ", " =====\n", new Token(
				SectionToken));
		rules[2] = new SingleLineRule("==== ", " ====\n", new Token(SectionToken));
		rules[3] = new SingleLineRule("=== ", " ===\n", new Token(SectionToken));
		rules[4] = new SingleLineRule("== ", " ==\n", new Token(SectionToken));
		rules[5] = new SingleLineRule("= ", " =\n", new Token(SectionToken));
		rules[6] = new MultiLineRule("{{{", "}}}", new Token(SourceToken));

		for (PatternRule rule : rules)
			rule.setColumnConstraint(0);

		setPredicateRules(rules);
	}

	public String[] getTokens() {
		return new String[] { SectionToken, SourceToken };
	}
}
