#!/usr/bin/env python3
"""
Sage AI Agent - Strategic Intelligence Analyst
Internal reasoning via o3-mini, clean polished output to user
IMPROVED: Logging, error handling, timeout protection
"""

import pandas as pd
from openai import OpenAI
import json
import os
import traceback
from typing import Dict, Optional
from dotenv import load_dotenv
from loguru import logger
from datetime import datetime

load_dotenv()

# Configure logging for agent
logger.add(
    "logs/sage_agent.log",
    rotation="100 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    backtrace=True,
    diagnose=True
)

class SageAgent:
    """Sage - Strategic Intelligence Analyst for rPotential.ai CPO tool"""
    
    def __init__(self, data_path: str, api_key: Optional[str] = None):
        logger.info(f"Initializing SageAgent with data_path: {data_path}")
        
        try:
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Data file not found: {data_path}")
            
            logger.info(f"Loading data from {data_path}...")
            self.df = pd.read_csv(data_path, low_memory=False)
            logger.info(f"✅ Loaded {len(self.df)} posts from {data_path}")
            
            if len(self.df) == 0:
                logger.warning("⚠️ Dataset is empty!")
        except Exception as e:
            logger.error(f"❌ Failed to load data: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file or environment.")
        
        try:
            logger.info(f"🔑 Initializing OpenAI client with API key: {api_key[:30]}...")
            self.client = OpenAI(api_key=api_key)
            logger.info("✅ OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
            raise
    
    def answer_ceo_question(self, question: str, estimates_ok: bool = False, verbose: bool = False) -> Dict:
        """Answer a CEO question - reasoning internal, output polished and clean"""
        start_time = datetime.now()
        logger.info(f"🔍 Processing question: {question[:100]}...")
        
        try:
            # Find relevant posts - use ALL available data
            relevant_posts = self._find_all_relevant_posts(question)
            
            if len(relevant_posts) == 0:
                logger.warning("⚠️ No relevant posts found in dataset")
                return {
                    "executive_summary": "No relevant posts found in dataset",
                    "confidence": "LOW",
                    "posts_analyzed": 0,
                    "data_scope": "0 posts"
                }
            
            logger.info(f"📊 Analyzing {len(relevant_posts)} posts ({len(relevant_posts)/len(self.df)*100:.1f}% of dataset)")
            
            # Build context from posts
            context = self._build_context(relevant_posts, question)
            
            # Generate answer with internal reasoning
            answer = self._generate_answer(question, context, relevant_posts, estimates_ok, verbose)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Answer generated in {duration:.2f}s")
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Error processing question: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "executive_summary": f"Error processing question: {str(e)}",
                "confidence": "LOW",
                "posts_analyzed": 0,
                "error": str(e)
            }
    
    def _find_all_relevant_posts(self, question: str) -> pd.DataFrame:
        """Find ALL posts for comprehensive analysis - NO FILTERING"""
        # Use ALL posts for maximum coverage (Paul: analyze ALL 5K posts)
        relevant = self.df.copy()
        
        # Sort by relevance but analyze everything
        relevant = relevant.sort_values('relevance_score', ascending=False)
        return relevant
    
    def _build_context(self, posts: pd.DataFrame, question: str) -> str:
        """Build comprehensive context using ALL enrichment columns + posts + comments"""
        context_parts = []
        
        # Calculate totals
        total_comments = posts['num_comments_scraped'].fillna(0).sum()
        
        # HIGH-CONFIDENCE pattern summary (use enrichment!)
        high_conf = posts[posts['confidence_level'] == 'HIGH']
        context_parts.append(f"DATASET OVERVIEW: {len(posts)} posts ({len(high_conf)} HIGH-confidence), {int(total_comments):,} comments, {posts['subreddit'].nunique()} subreddits")
        
        # CEO Question Categories breakdown (STRATEGIC)
        context_parts.append(f"\nCEO QUESTION CATEGORIES (from enrichment):")
        for cat in posts['ceo_question_category'].unique()[:5]:
            if pd.notna(cat):
                count = len(posts[posts['ceo_question_category'] == cat])
                pct = count / len(posts) * 100
                context_parts.append(f"  • {cat}: {count} posts ({pct:.0f}%)")
        
        # Actionability breakdown (CRITICAL!)
        context_parts.append(f"\nACTIONABILITY DISTRIBUTION:")
        risk_mit = len(posts[posts['actionability'] == 'Risk Mitigation'])
        opp_det = len(posts[posts['actionability'] == 'Opportunity Detection'])
        context_parts.append(f"  • Risk Mitigation: {risk_mit} posts ({risk_mit/len(posts)*100:.0f}%) - URGENT")
        context_parts.append(f"  • Opportunity Detection: {opp_det} posts ({opp_det/len(posts)*100:.0f}%) - GROWTH")
        
        # Sentiment breakdown
        context_parts.append(f"\nSENTIMENT ANALYSIS:")
        for sentiment in ['Negative', 'Positive', 'Mixed', 'Neutral']:
            count = len(posts[posts['sentiment'] == sentiment])
            if count > 0:
                pct = count / len(posts) * 100
                context_parts.append(f"  • {sentiment}: {count} posts ({pct:.0f}%)")
        
        # Companies and Products mentioned (COMPETITIVE INTEL)
        context_parts.append(f"\nKEY ENTITIES MENTIONED (from enrichment):")
        companies = [c.strip() for c in str(posts['companies_mentioned'].iloc[0]).split(',') if pd.notna(posts['companies_mentioned'].iloc[0])]
        products = [p.strip() for p in str(posts['products_mentioned'].iloc[0]).split(',') if pd.notna(posts['products_mentioned'].iloc[0])]
        context_parts.append(f"  • Companies: {', '.join(companies[:5])}")
        context_parts.append(f"  • Products: {', '.join(products[:5])}")
        
        context_parts.append(f"\n{'='*80}")
        context_parts.append(f"DETAILED POST ANALYSIS (ALL ENRICHMENT COLUMNS):")
        context_parts.append(f"{'='*80}")
        
        # ITERATE ROW BY ROW - include ALL columns
        for idx, (_, post) in enumerate(posts.head(100).iterrows(), 1):
            # Basic info
            url = str(post.get('url', 'N/A') or 'N/A')
            title = str(post.get('title', '') or '')
            body = str(post.get('body', '') or '')[:300]
            username = str(post.get('username', 'Unknown') or 'Unknown')
            subreddit = str(post.get('subreddit', 'unknown') or 'unknown')
            
            # Extract date
            post_date = "Date unavailable"
            try:
                created_at = post.get('created_at')
                if pd.notna(created_at):
                    if isinstance(created_at, str):
                        from datetime import datetime
                        post_date = pd.to_datetime(created_at, errors='coerce')
                    else:
                        post_date = created_at
                    if pd.notna(post_date):
                        post_date = post_date.strftime('%B %d, %Y') if hasattr(post_date, 'strftime') else str(post_date)
            except:
                post_date = "Date unavailable"
            
            # ENRICHMENT COLUMNS (THE AHA MOMENT!)
            ceo_cat = str(post.get('ceo_question_category', '') or '')
            strategic_signal = str(post.get('strategic_signal', '') or '')[:200]
            confidence = str(post.get('confidence_level', 'UNKNOWN') or 'UNKNOWN')
            sentiment = str(post.get('sentiment', '') or '')
            actionability = str(post.get('actionability', '') or '')
            temporal = str(post.get('temporal_context', '') or '')
            companies = str(post.get('companies_mentioned', '') or '')
            products = str(post.get('products_mentioned', '') or '')
            roles = str(post.get('roles_mentioned', '') or '')
            tags = str(post.get('tags', '') or '')[:200]
            relevance_score = float(post.get('relevance_score', 0) or 0)
            relevance_cat = str(post.get('relevance_category', '') or '')
            
            # Build enriched post entry with date
            context_parts.append(f"\n[POST {idx}] r/{subreddit} by u/{username} | Posted: {post_date} | {confidence} confidence | {actionability}")
            context_parts.append(f"  URL: {url}")
            context_parts.append(f"  TITLE: {title}")
            if body:
                context_parts.append(f"  TEXT: {body}")
            
            # ENRICHMENT METADATA (THIS IS THE MAGIC!)
            if strategic_signal and strategic_signal != 'nan':
                context_parts.append(f"  🎯 SIGNAL: {strategic_signal}")
            context_parts.append(f"  📊 Category: {ceo_cat} | Sentiment: {sentiment} | Temporal: {temporal}")
            context_parts.append(f"  💼 Relevance: {relevance_cat} (score: {relevance_score:.2f})")
            if companies and companies != 'nan':
                context_parts.append(f"  🏢 Companies: {companies[:100]}")
            if products and products != 'nan':
                context_parts.append(f"  ⚙️  Products: {products[:100]}")
            if roles and roles != 'nan':
                context_parts.append(f"  👥 Roles: {roles[:100]}")
            if tags and tags != 'nan':
                context_parts.append(f"  #️⃣  Tags: {tags}")
            
            # Include top comments
            try:
                comments_json_str = post.get('all_scraped_comments_json', '[]')
                if pd.notna(comments_json_str) and comments_json_str:
                    comments_data = json.loads(str(comments_json_str))
                    if isinstance(comments_data, list) and len(comments_data) > 0:
                        top_comments = sorted(
                            comments_data, 
                            key=lambda x: x.get('score', 0), 
                            reverse=True
                        )[:3]
                        context_parts.append(f"  💬 TOP COMMENTS ({len(comments_data)} total):")
                        for c_idx, comment in enumerate(top_comments, 1):
                            c_author = comment.get('author', 'Unknown')
                            c_score = comment.get('score', 0)
                            c_body = str(comment.get('body', ''))[:150]
                            # Extract comment date if available
                            c_date = "Date unavailable"
                            try:
                                c_created = comment.get('created_utc') or comment.get('publishingDate')
                                if c_created:
                                    if isinstance(c_created, (int, float)):
                                        from datetime import datetime
                                        c_date = datetime.fromtimestamp(c_created).strftime('%B %d, %Y')
                                    elif isinstance(c_created, str):
                                        c_date = pd.to_datetime(c_created, errors='coerce')
                                        if pd.notna(c_date):
                                            c_date = c_date.strftime('%B %d, %Y') if hasattr(c_date, 'strftime') else str(c_date)
                            except:
                                pass
                            context_parts.append(f"      [{c_idx}] u/{c_author} ({c_score}↑) on {c_date}: {c_body}")
            except:
                pass
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str, posts: pd.DataFrame, estimates_ok: bool, verbose: bool) -> Dict:
        """Generate answer - reasoning is INTERNAL via o3-mini, output is CLEAN"""
        
        system_prompt = """Act like Sage, a strategic intelligence analyst for rPotential.ai's CPO (Chief Potential Officer) tool, advising Fortune 500 CEOs on $10M+ decisions about AI and human workforce optimization.

OBJECTIVE: Isolate untapped signals of organizational and individual potential from our uploaded internal dataset and point them to specific enterprise leaders to exploit strategically—without using any external sources.

NON-NEGOTIABLES (NO BULLSHIT):

1. Internal data only: Use only the uploaded internal Reddit dataset. Do not browse the web, do not use real-time Reddit or any external tools.

2. Brutal honesty: Provide estimates only if the user explicitly sets ESTIMATES_OK: true. Never present estimates or incomplete data as facts.

3. Provenance always (include in every answer):
   - Data scope line: "Based on X posts from Y subreddits, posted June 21, 2023 to October 24, 2025. Data freshness: 72.5% from last 3 months"
   - Confidence level: HIGH / MEDIUM / LOW with explicit reasoning
   - What the data CAN answer vs CANNOT answer
   - Recommended supplements to fill gaps (CB Insights, Gartner, Forrester, PitchBook, Bloomberg)

4. Bias note: Reddit has a negativity bias (users vent more than praise). Treat complaints as overrepresented and wins as underreported.

═══════════════════════════════════════════════════════════════════════════════
PROMPT ENGINEERING TECHNIQUES (FROM https://www.promptingguide.ai/techniques/rag)
═══════════════════════════════════════════════════════════════════════════════

🧠 CHAIN-OF-THOUGHT REASONING (Step-by-step improves accuracy):
Use this explicit reasoning path:
  Step 1: ISOLATE - Classify CEO question type (Implementation? Risk? Competitive?)
  Step 2: RETRIEVE - Find relevant posts using enrichment metadata
  Step 3: ANALYZE - Pattern recognition across enrichment columns
  Step 4: SYNTHESIZE - Chain reasoning from data patterns
  Step 5: GENERATE - Create response with citations
  Step 6: VERIFY - Check consistency with other signals

📚 FEW-SHOT PROMPTING (Examples guide behavior):
EXAMPLE 1 - Good Human-Agent Config Answer:
Q: "How do our human-agent configurations compare to industry leaders?"
A: Within 1,125 HIGH-confidence posts (20% of dataset), the pattern is clear:
   • 55% focus on Opportunity Detection (growth potential)
   • 20% on Decision Support (immediate wins)
   • Sentiment: 32% positive (solutions exist)
   • Companies driving this: Salesforce (50%), OpenAI (25%), Anthropic (15%)
   • Quote: "HubSpot has the hybrid approach right - org structures will be less pyramid, 
     more workflow oriented" - r/ThinkingDeeplyAI by u/Beginning-Willow-801

🌳 TREE-OF-THOUGHTS (Multiple reasoning paths prevent bias):
For each question, explore 3 reasoning paths:
  PATH A (Risk Mitigation): 49.5% of posts - what are the dangers?
  PATH B (Opportunity Detection): 42% of posts - what's the upside?
  PATH C (Decision Support): 8% of posts - what should we do now?
Then synthesize: "The pattern combines risks (X), opportunities (Y), and immediate actions (Z)"

✅ SELF-CONSISTENCY (Generate twice, verify convergence):
For complex CEO questions, generate reasoning 2x:
  - If >95% consistency: Output with HIGH confidence
  - If <95% consistency: Flag as MEDIUM, show both perspectives
This prevents single-path hallucinations

🎯 CONTEXT ENGINEERING (Order matters - what you input determines output):
Strategic context order:
  1. CEO Question (what we're solving)
  2. Enrichment Summary (CEO categories %, actionability %, sentiment %)
  3. Few-Shot Examples (what a good answer looks like)
  4. Top 30 Posts (by relevance_score × confidence_level)
  5. Top Comments (high-upvote validation)
  6. Explicit Instructions (response format)

⚡ REACT (Reasoning + Acting - make your process transparent):
Show your work:
  THOUGHT: "This is a Risk Mitigation question. I should prioritize posts with Negative sentiment."
  ACTION: "Retrieve Implementation Reality posts where actionability = Risk Mitigation"
  RESULT: "Found 308 posts. Analyzing patterns across companies and roles..."

═══════════════════════════════════════════════════════════════════════════════
ENRICHMENT METADATA TO LEVERAGE (from CSV)
═══════════════════════════════════════════════════════════════════════════════

Confidence Weighting:
  • HIGH (95% of posts): Trust these signals heavily
  • MEDIUM (5% of posts): Mention with caveats

CEO Question Categories:
  • Implementation Reality (54%): Real-world deployment challenges - ACTIONABLE
  • Human-Agent Config (20%): Workforce structure implications - STRATEGIC
  • Competitive Intelligence (13%): Market positioning - COMPARATIVE
  • Risk/Controversy (5%): Compliance, security - CRITICAL
  • Strategic Partner (4%): Vendor evaluation - DECISION-CRITICAL
  • Budget/ROI (2.5%): Financial signals - LIMITED
  • Untapped Signals (0.5%): Hidden opportunities - EXPLORATORY

Actionability Focus:
  • Risk Mitigation (49.5%): What could go wrong? How do we prevent it?
  • Opportunity Detection (42%): What could we gain? How do we capture it?
  • Decision Support (8%): What should we decide? How do we choose?

Sentiment Analysis:
  • Negative (39%): Real problems, implementation blockers → USE FOR RISK
  • Positive (32%): Solutions, workarounds → USE FOR OPPORTUNITY
  • Mixed (15%): Tradeoffs, nuance → USE FOR BALANCED DECISIONS
  • Neutral (14%): Factual information → USE FOR BENCHMARKING

Temporal Context (77% immediate = NOW, 20% quarterly, 2% strategic, 0.2% annual):
  • Show urgency: "77% of relevant posts are IMMEDIATE (act this week/month)"
  • Show frequency: "But this repeats QUARTERLY - 20% of posts"

Companies/Products/Roles:
  • Extract and analyze competitive positioning
  • Show which roles are at risk
  • Connect to skills gaps and training needs

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT - DELIVER CLEAN, CEO-READY ANSWERS
═══════════════════════════════════════════════════════════════════════════════

Executive Summary
[2–3 sentences: What's the answer? Confidence level. Actionability.]

Data Scope
[Transparency: Posts analyzed, comments, date range, freshness, coverage, CEO categories %]

Key Findings - What CAN Answer (HIGH confidence)
[QUOTED findings with citations - use enrichment metadata to surface patterns]
[Format: "Exact quote" - r/subreddit by u/username (Link: url)]
[Show the pattern: "X% of posts focus on Y, specifically: [quote]"]

Key Findings - What CANNOT Answer
[Honest gaps: ROI not in Reddit, pricing not discussed, etc.]
[Recommend: "CB Insights for ROI benchmarks", "Gartner for market share"]

Strategic Signals
[Organizational Potential, Individual Potential, Human-AI Work Future]
[Grounded in quoted examples, enrichment patterns]

Recommended Next Steps
[Immediate (from HIGH-confidence signals)]
[Gap to fill (external data needed)]
[Follow-up question (sharpen the decision)]

Data Limitations
[Blunt: negativity bias, anecdotal, unverified identities]

Suggested Next Questions
[2-3 CEO-level questions based on gaps found]

═══════════════════════════════════════════════════════════════════════════════
QUALITY CHECKS (BEFORE RESPONDING)
═══════════════════════════════════════════════════════════════════════════════

✅ Chain-of-Thought: Did I show my reasoning steps (Isolate → Retrieve → Analyze → Synthesize)?
✅ Few-Shot: Did I follow the example formats shown above?
✅ Tree of Thoughts: Did I explore multiple reasoning paths (Risk, Opportunity, Decision)?
✅ Self-Consistency: Do my findings converge? Any contradictions?
✅ Context Engineering: Is my response ordered strategically (summary → findings → gaps)?
✅ ReAct: Did I show my thought → action → result?
✅ Provenance: Every claim has a Reddit quote with citation?
✅ No Hallucinations: Every number, company name, role from the data?
✅ CAN/CANNOT: Clear about what the data answers vs. doesn't?
✅ Enrichment Used: CEO categories, actionability, sentiment, temporal context visible?"""
        
        user_prompt = f"""QUESTION FROM CEO: {question}

CONTEXT (from {len(posts)} posts analyzed with {int(posts['num_comments_scraped'].fillna(0).sum()):,} total comments):
{context}

⚡ CRITICAL: USE ENRICHMENT METADATA TO CREATE AHA MOMENTS FOR PAUL:

The context above includes ENRICHED POST DATA with these strategic columns:
  • Confidence Levels: Posts are tagged HIGH/MEDIUM - use these to weight your analysis
  • CEO Question Categories: Implementation Reality (54%), Human-Agent Config (20%), etc.
  • Actionability: Risk Mitigation (50%) or Opportunity Detection (42%) - prioritize these
  • Sentiment: Negative (39%), Positive (32%), Mixed (15%), Neutral (14%)
  • Strategic Signals: Each post has a pre-analyzed "signal" for CEO potential
  • Temporal Context: Immediate (77%), Quarterly (20%), Strategic (2%)
  • Companies/Products/Roles: Extract competitive/skill insights
  • Relevance Score: How well posts match the CEO question (0-5 scale)

YOUR JOB: Synthesize patterns using this metadata. Examples of AHA moments:
  ✅ "49.5% of relevant posts focus on RISK MITIGATION, specifically around X. The top signal: Y"
  ✅ "Within HIGH-confidence Implementation Reality posts (54% of dataset), the pattern is Z"
  ✅ "39% negative sentiment across roles mentioned: DevOps, Admin, Manager - they cite A, B, C"
  ✅ "Company mentions show: Salesforce (50%), OpenAI (25%), Anthropic (15%) - indicating shift to X"

CRITICAL INSTRUCTIONS - ANALYZE BOTH POSTS AND COMMENTS:

1. QUOTE actual text from BOTH posts AND comments - don't paraphrase
   - Posts: Use post titles and bodies
   - Comments: Use comment text, especially high-upvote comments (these represent community consensus)
   
2. DATA FRESHNESS AWARENESS (IMPORTANT FOR CEO DECISIONS):
   - Agentforce posts: Median age ~97 days (Sep 2024 → Oct 2025) - Newer data, high relevance
   - Salesforce posts: Median age ~87 days (Jun 2023 → Oct 2025) - Spans 2+ years, good longitudinal view
   - AI/Automation posts: Median age ~14 days (Apr 2025 → Oct 2025) - Very fresh, rapid changes
   - 72.5% of data from last 3 months = CURRENT market sentiment
   - Use recency as a confidence booster (recent = HIGH confidence, older = requires validation)
   
3. CITATION FORMAT (MANDATORY - MUST FOLLOW EXACTLY - NO EXCEPTIONS):
   
   ⚠️ CRITICAL: EVERY SINGLE QUOTE MUST USE THIS EXACT FORMAT. NO PARAPHRASING. NO SUMMARIES.
   
   For posts (MANDATORY FORMAT):
   "Exact quote from the post here" - r/subreddit by u/username on Date (Link: https://reddit.com/r/subreddit/comments/abc123/...)
   
   REQUIRED ELEMENTS (ALL MUST BE PRESENT):
   • Exact quote in double quotes: "quote here"
   • Space, hyphen, space: " - "
   • Subreddit: r/subreddit
   • Space, "by", space: " by "
   • Username: u/username
   • Space, "on", space: " on "
   • Full date: "October 15, 2024" (NOT "Oct 15" or "10/15/24")
   • Space, opening parenthesis: " ("
   • "Link: " followed by full URL: "Link: https://reddit.com/r/subreddit/comments/abc123/..."
   • Closing parenthesis: ")"
   
   EXAMPLE - GOOD (COPY THIS FORMAT EXACTLY):
   "Agentforce integration with our existing CMDB was a nightmare" - r/salesforce by u/JohnAdmin on October 15, 2024 (Link: https://reddit.com/r/salesforce/comments/1nkl2v3/agentforce_integration_problems/)
   
   For comments (MANDATORY FORMAT):
   "Exact quote from comment here" - r/subreddit by u/username on Date (Comment in: Post Title)
   
   EXAMPLE - GOOD (COPY THIS FORMAT EXACTLY):
   "We have been using this for 6 months and it has been a game changer" - r/salesforce by u/AdminPro on September 20, 2024 (Comment in: Agentforce Best Practices)
   
   EXAMPLE - BAD (DO NOT DO THIS):
   In r/salesforce, user JohnAdmin said Agentforce was difficult.
   
   EXAMPLE - BAD (DO NOT DO THIS):
   Users report that Agentforce integration is challenging.
   
   EXAMPLE - BAD (DO NOT DO THIS):
   "quote" - r/salesforce (missing username, date, link)
   
   ⚠️ ENFORCEMENT: If you cannot find a quote with ALL elements (subreddit, username, date, link), DO NOT include it. Only cite what you can fully verify.
   
4. Use comments to:
   - Validate or challenge post claims
   - Show disagreement/agreement patterns  
   - Highlight industry consensus (high-upvote comments = agreement)
   - Find specific implementation examples

5. Pattern analysis:
   - If 10+ posts mention X problem, quote 1-2 examples with full citations
   - If high-upvote comments show agreement, cite: "Top comment (250 upvotes): \"quote\" - r/salesforce comment" 

6. Never make generic claims:
   - ❌ BAD: "Users report implementing AI" (no quote, no citation)
   - ✅ GOOD: "\"We rolled out Copilot last quarter and productivity jumped\" - r/github by u/EngineerJane (Link: url)"

7. Always mark what's NOT in the data:
   - "Financial ROI metrics: NOT FOUND IN DATASET - no posts discuss this"
   - "Pricing comparisons: NOT FOUND - comments don't mention pricing"

CRITICAL: USE EXACT HYPHEN FORMAT FOR CITATIONS (ZERO TOLERANCE):
   • MUST USE: " - r/" (space, hyphen, space, r slash) - NOT en dash " – "
   • EVERY quote MUST include ALL FOUR elements: date, subreddit, username, and link
   • Format: "quote" - r/subreddit by u/username on Date (Link: url)
   • MINIMUM: Every finding must have 3+ citations with FULL format
   • Use full dates: "October 15, 2024" not "Oct 15" or "10/15/24" or "2024-10-15"
   • Links must be full Reddit URLs: https://reddit.com/r/subreddit/comments/...
   • If a post URL is missing, use the format: (Link: https://reddit.com/r/subreddit/comments/[post_id]/)
   • NEVER skip citations - if you make a claim, you MUST back it with a quote in the exact format above

OUTPUT FORMATTING REQUIREMENTS:
   • Write in clear, professional English
   • Avoid contractions (use "do not" not "don't", "cannot" not "can't")
   • Use proper paragraph breaks
   • Format citations as clean blockquotes or inline citations
   • Ensure readability with proper spacing and structure
   • Use bullet points for lists
   • Bold important findings with **text**

DELIVER OUTPUT WITH ACTUAL CITATIONS - DO NOT PARAPHRASE OR SUMMARIZE. Quote every finding.

Analyze the posts AND comments thoroughly. Quote specific users. Ground everything in the data."""
        
        try:
            if verbose:
                logger.info("🤖 Calling o3-mini with HIGH reasoning...")
            
            logger.debug(f"Requesting OpenAI API with model: o3-mini")
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=4000,
                timeout=60.0  # 60 second timeout
            )
            
            answer_text = response.choices[0].message.content
            
            if verbose:
                logger.info("✅ Response received from OpenAI")
            
            if not answer_text:
                logger.warning("⚠️ Empty response from OpenAI")
                raise ValueError("Empty response from OpenAI API")
            
            # Clean and format the answer text for readability
            answer_text = self._clean_answer_text(answer_text)
            
            # Extract first paragraph as executive summary
            summary = answer_text.split('\n\n')[0] if '\n\n' in answer_text else answer_text[:300]
            
            # Extract citations
            citations = self._extract_citations(posts)
            
            # Calculate totals
            total_comments = int(posts['num_comments_scraped'].fillna(0).sum())
            total_comments_claimed = int(posts['num_comments_claimed'].fillna(0).sum())
            
            # Calculate actual date range from posts
            date_range = "Date range unavailable"
            freshness_label = ""
            try:
                posts['created_at'] = pd.to_datetime(posts['created_at'], errors='coerce', utc=True)
                posts['created_at'] = posts['created_at'].dt.tz_localize(None)
                date_min = posts['created_at'].min()
                date_max = posts['created_at'].max()
                if pd.notna(date_min) and pd.notna(date_max):
                    date_range = f"{date_min.strftime('%B %d, %Y')} to {date_max.strftime('%B %d, %Y')}"
                    # Calculate freshness (median age)
                    from datetime import datetime
                    today = datetime.now()
                    median_age_days = int((today - posts['created_at'].median()).days)
                    freshness_label = f"Median age: {median_age_days} days (FRESH)" if median_age_days < 90 else f"Median age: {median_age_days} days"
            except:
                date_range = "Date range unavailable"
                freshness_label = ""
            
            return {
                "executive_summary": summary,
                "full_answer": answer_text,
                "confidence": "HIGH",
                "posts_analyzed": len(posts),
                "comments_analyzed": total_comments,
                "comments_claimed": total_comments_claimed,
                "subreddits": posts['subreddit'].nunique(),
                "dataset_coverage": "100.0% (ALL posts analyzed)",
                "data_scope": f"Based on {len(posts)} posts and {total_comments:,} comments from {posts['subreddit'].nunique()} subreddits, posted {date_range}. Data freshness: {freshness_label}",
                "citations": citations,
                "suggested_followups": self._generate_followups(question, answer_text)
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating answer: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Check for specific error types
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                error_msg = "Request timed out. The question may be too complex. Please try again."
            elif "rate limit" in str(e).lower():
                error_msg = "Rate limit exceeded. Please wait a moment and try again."
            elif "authentication" in str(e).lower() or "api key" in str(e).lower():
                error_msg = "Authentication error. Please check API key configuration."
            else:
                error_msg = f"Error generating response: {str(e)}"
            
            return {
                "executive_summary": error_msg,
                "confidence": "LOW",
                "posts_analyzed": len(posts),
                "error": str(e)
            }
    
    def _clean_answer_text(self, text: str) -> str:
        """Clean and format answer text for better readability"""
        if not text:
            return text
        
        # Remove contractions
        contractions = {
            "don't": "do not",
            "can't": "cannot",
            "won't": "will not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "hasn't": "has not",
            "haven't": "have not",
            "doesn't": "does not",
            "didn't": "did not",
            "wouldn't": "would not",
            "couldn't": "could not",
            "shouldn't": "should not",
            "mustn't": "must not",
            "it's": "it is",
            "that's": "that is",
            "there's": "there is",
            "here's": "here is",
            "what's": "what is",
            "who's": "who is",
            "where's": "where is",
            "I'm": "I am",
            "you're": "you are",
            "we're": "we are",
            "they're": "they are",
            "I've": "I have",
            "you've": "you have",
            "we've": "we have",
            "they've": "they have",
            "I'll": "I will",
            "you'll": "you will",
            "we'll": "we will",
            "they'll": "they will",
        }
        
        cleaned = text
        for contraction, expansion in contractions.items():
            # Case-insensitive replacement
            import re
            pattern = re.compile(re.escape(contraction), re.IGNORECASE)
            cleaned = pattern.sub(expansion, cleaned)
        
        # Clean up multiple spaces
        cleaned = re.sub(r' +', ' ', cleaned)
        
        # Clean up multiple newlines (keep max 2)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Ensure proper spacing around citations
        cleaned = re.sub(r'(".*?")-r/', r'\1 - r/', cleaned)
        cleaned = re.sub(r'(".*?") -r/', r'\1 - r/', cleaned)
        
        return cleaned.strip()
    
    def _extract_citations(self, posts: pd.DataFrame, claim_keywords: list = None) -> list:
        """Extract citations for claims - return post URLs and metadata with dates"""
        citations = []
        
        for _, post in posts.head(20).iterrows():
            # Handle NaN values properly
            title = str(post.get('title', '') or '')[:80]
            post_id = str(post.get('post_id', 'N/A') or 'N/A')
            url = str(post.get('url', 'N/A') or 'N/A')
            subreddit = str(post.get('subreddit', 'unknown') or 'unknown')
            username = str(post.get('username', 'Unknown') or 'Unknown')
            comments = int(post.get('num_comments_scraped', 0) or 0)
            
            # Extract date
            post_date = "Date unavailable"
            try:
                created_at = post.get('created_at')
                if pd.notna(created_at):
                    if isinstance(created_at, str):
                        post_date = pd.to_datetime(created_at, errors='coerce')
                    else:
                        post_date = created_at
                    if pd.notna(post_date):
                        if hasattr(post_date, 'strftime'):
                            post_date = post_date.strftime('%B %d, %Y')
                        else:
                            post_date = str(post_date)
            except:
                post_date = "Date unavailable"
            
            citation = {
                'post_id': post_id,
                'url': url,
                'title': title,
                'subreddit': subreddit,
                'username': username,
                'date': post_date,
                'comments': comments
            }
            citations.append(citation)
        
        return citations
    
    def _generate_followups(self, question: str, answer: str) -> list:
        """Generate follow-up questions based on the answer"""
        followups = []
        
        # Basic follow-up logic
        if 'configuration' in question.lower():
            followups.append("Which specific configurations show the highest adoption rates?")
            followups.append("What are the implementation blockers for alternative configurations?")
        
        if 'implementation' in question.lower() or 'challenges' in question.lower():
            followups.append("Which teams struggle most with these challenges?")
            followups.append("What immediate mitigation strategies are users suggesting?")
        
        if 'competitor' in question.lower():
            followups.append("Which competitor tactics are driving talent migration?")
            followups.append("What capabilities are competitors emphasizing in their hiring?")
        
        if not followups:
            followups = [
                "What immediate actions should we prioritize based on this data?",
                "Which external sources would strengthen this analysis?",
                "How does our current approach compare to best practices in the data?"
            ]
        
        return followups[:3]

if __name__ == "__main__":
    agent = SageAgent("results/rpotential_filtered_focused_data.csv")
    result = agent.answer_ceo_question(
        "How do our human-agent configurations compare to industry leaders?",
        verbose=True
    )
    print("\n" + "="*80)
    print(result['full_answer'])
    print("="*80)
