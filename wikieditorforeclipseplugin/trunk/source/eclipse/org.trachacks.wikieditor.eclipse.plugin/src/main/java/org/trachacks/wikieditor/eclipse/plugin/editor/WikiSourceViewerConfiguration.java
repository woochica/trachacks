package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.TextAttribute;
import org.eclipse.jface.text.contentassist.ContentAssistant;
import org.eclipse.jface.text.contentassist.IContentAssistant;
import org.eclipse.jface.text.presentation.IPresentationReconciler;
import org.eclipse.jface.text.presentation.PresentationReconciler;
import org.eclipse.jface.text.rules.DefaultDamagerRepairer;
import org.eclipse.jface.text.rules.IRule;
import org.eclipse.jface.text.rules.IToken;
import org.eclipse.jface.text.rules.ITokenScanner;
import org.eclipse.jface.text.rules.RuleBasedScanner;
import org.eclipse.jface.text.rules.SingleLineRule;
import org.eclipse.jface.text.rules.Token;
import org.eclipse.jface.text.source.ISharedTextColors;
import org.eclipse.jface.text.source.ISourceViewer;
import org.eclipse.jface.text.source.SourceViewerConfiguration;
import org.eclipse.swt.SWT;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.graphics.RGB;

public class WikiSourceViewerConfiguration extends SourceViewerConfiguration {
	private WikiSourceEditor editor;

	private final ISharedTextColors colors;

	private static final RGB ColorSource = new RGB(100, 100, 100);

	public WikiSourceViewerConfiguration(WikiSourceEditor editor,
			ISharedTextColors colors) {
		this.editor = editor;
		this.colors = colors;
	}

	/*
	 * @seeorg.eclipse.jface.text.source.SourceViewerConfiguration#
	 * getPresentationReconciler(org.eclipse.jface.text.source.ISourceViewer)
	 */
	public IPresentationReconciler getPresentationReconciler(
			ISourceViewer sourceViewer) {
		PresentationReconciler reconciler = new PresentationReconciler();
		DefaultDamagerRepairer dr = new DefaultDamagerRepairer(
				getDefaultScanner());
		reconciler.setDamager(dr, IDocument.DEFAULT_CONTENT_TYPE);
		reconciler.setRepairer(dr, IDocument.DEFAULT_CONTENT_TYPE);

		reconciler.setDamager(dr, WikiPartitionScanner.SectionToken);
		reconciler.setRepairer(dr, WikiPartitionScanner.SectionToken);

		TextAttribute attr = new TextAttribute(colors.getColor(ColorSource));
		NonRuleBasedDamagerRepairer nr = new NonRuleBasedDamagerRepairer(attr);
		reconciler.setDamager(nr, WikiPartitionScanner.SourceToken);
		reconciler.setRepairer(nr, WikiPartitionScanner.SourceToken);

		return reconciler;
	}

	private ITokenScanner getDefaultScanner() {
		RuleBasedScanner scanner = new RuleBasedScanner();

		IRule[] rules = new IRule[14];
		rules[0] = createHeader6Rule();
		rules[1] = createHeader5Rule();
		rules[2] = createHeader4Rule();
		rules[3] = createHeader3Rule();
		rules[4] = createHeader2Rule();
		rules[5] = createHeader1Rule();
		rules[6] = createHRRule();
		rules[7] = createMacroRule();
		rules[8] = createExternalHTTPRule();
		rules[9] = createListRule();
		rules[10] = createNumberedListRule();
		rules[11] = createBoldItalicRule();
		rules[12] = createBoldRule();
		rules[13] = createItalicRule();

		scanner.setRules(rules);
		return scanner;
	}

	private IRule createBoldRule() {
		Color color = colors.getColor(new RGB(0, 0, 0));
		IToken boldToken = new Token(new TextAttribute(color, null, SWT.BOLD));
		SingleLineRule singleLineRule = new SingleLineRule("'''", "'''",
				boldToken);
		return singleLineRule;
	}

	private IRule createItalicRule() {
		Color color = colors.getColor(new RGB(0, 0, 0));
		IToken italicToken = new Token(new TextAttribute(color, null,
				SWT.ITALIC));
		SingleLineRule singleLineRule = new SingleLineRule("''", "''",
				italicToken);
		return singleLineRule;
	}

	private IRule createBoldItalicRule() {
		Color color = colors.getColor(new RGB(0, 0, 0));
		TextAttribute attr = new TextAttribute(color, null, SWT.BOLD
				| SWT.ITALIC);
		IToken token = new Token(attr);
		SingleLineRule rule = new SingleLineRule("'''''", "'''''", token);
		return rule;
	}

	private IRule createHRRule() {
		Color color = colors.getColor(new RGB(0, 0, 140));
		IToken token = new Token(new TextAttribute(color, null, SWT.NONE));
		SingleLineRule rule = new SingleLineRule("----", "\n", token);
		rule.setColumnConstraint(0);
		return rule;
	}

	private IRule createHeader1Rule() {
		Color color = colors.getColor(new RGB(0, 0, 140));
		IToken token = new Token(new TextAttribute(color, null, SWT.BOLD));
		SingleLineRule rule = new SingleLineRule("=", "=\n", token);
		rule.setColumnConstraint(0);
		return rule;
	}

	private IRule createHeader2Rule() {
		Color color = colors.getColor(new RGB(0, 0, 140));
		IToken token = new Token(new TextAttribute(color, null, SWT.BOLD));
		SingleLineRule rule = new SingleLineRule("==", "==\n", token);
		rule.setColumnConstraint(0);
		return rule;
	}

	private IRule createHeader3Rule() {
		Color color = colors.getColor(new RGB(0, 0, 140));
		IToken token = new Token(new TextAttribute(color, null, SWT.NONE));
		SingleLineRule rule = new SingleLineRule("===", "===\n", token);
		rule.setColumnConstraint(0);
		return rule;
	}

	private IRule createHeader4Rule() {
		Color color = colors.getColor(new RGB(0, 0, 140));
		IToken token = new Token(new TextAttribute(color, null, SWT.NONE));
		SingleLineRule rule = new SingleLineRule("====", "====\n", token);
		rule.setColumnConstraint(0);
		return rule;
	}

	private IRule createHeader5Rule() {
		Color color = colors.getColor(new RGB(0, 0, 140));
		IToken token = new Token(new TextAttribute(color, null, SWT.NONE));
		SingleLineRule rule = new SingleLineRule("=====", "=====\n", token);
		rule.setColumnConstraint(0);
		return rule;
	}

	private IRule createHeader6Rule() {
		Color color = colors.getColor(new RGB(0, 0, 140));
		IToken token = new Token(new TextAttribute(color, null, SWT.NONE));
		SingleLineRule rule = new SingleLineRule("======", "======\n", token);
		rule.setColumnConstraint(0);
		return rule;
	}

	private IRule createListRule() {
		Color color = colors.getColor(new RGB(63, 127, 95));
		IToken dashToken = new Token(new TextAttribute(color, null, SWT.NONE));
		SingleLineRule singleLineRule = new SingleLineRule(" * ", "\n",
				dashToken);
		return singleLineRule;
	}

	private IRule createNumberedListRule() {
		Color color = colors.getColor(new RGB(63, 127, 95));
		IToken dashToken = new Token(new TextAttribute(color, null, SWT.NONE));
		SingleLineRule singleLineRule = new SingleLineRule("#", "\n", dashToken);
		singleLineRule.setColumnConstraint(0);
		return singleLineRule;
	}

	private IRule createMacroRule() {
		Color color = colors.getColor(new RGB(200, 100, 100));
		IToken token = new Token(new TextAttribute(color, null, SWT.NONE));
		SingleLineRule rule = new SingleLineRule("[[", "]]", token);
		return rule;
	}

	private IRule createExternalHTTPRule() {
		Color color = colors.getColor(new RGB(200, 100, 100));
		IToken token = new Token(new TextAttribute(color, null, SWT.NONE));
		SingleLineRule rule = new SingleLineRule("[http", "]", token);
		return rule;
	}

	@Override
	public IContentAssistant getContentAssistant(ISourceViewer sourceViewer) {
		ContentAssistant assistant = new ContentAssistant();
		assistant.enableAutoActivation(true);
		assistant.setAutoActivationDelay(500);
		assistant.setContentAssistProcessor(
				new WikiCompletionProcessor(editor),
				IDocument.DEFAULT_CONTENT_TYPE);
		return assistant;
	}

	// //////////////////////////////////////////////////////////////////

}
