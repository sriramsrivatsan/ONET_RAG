"""
Landing Page for Labor Market RAG Application
Professional start page with company branding and navigation
"""
import streamlit as st
import os
from pathlib import Path
from app.ui.landing_config import LANDING_CONFIG


class LandingPage:
    """Professional landing page with company branding"""
    
    def __init__(self):
        self.config = LANDING_CONFIG
        
    def render(self):
        """Render the landing page"""
        
        # Add custom CSS for professional styling
        st.markdown("""
        <style>
            /* Main container styling */
            .landing-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            /* Logo styling */
            .logo-container {
                text-align: center;
                margin-bottom: 2rem;
                padding: 2rem 0;
            }
            
            /* Title styling */
            .main-title {
                text-align: center;
                font-size: 3rem;
                font-weight: 700;
                color: #1E3A8A;
                margin-bottom: 1rem;
                line-height: 1.2;
            }
            
            /* Tagline styling */
            .tagline {
                text-align: center;
                font-size: 1.5rem;
                color: #3B82F6;
                margin-bottom: 1rem;
            }
            
            /* Description styling */
            .description {
                text-align: center;
                font-size: 1.1rem;
                color: #4B5563;
                max-width: 800px;
                margin: 0 auto 3rem auto;
                line-height: 1.6;
            }
            
            /* Button card styling */
            .button-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                padding: 2rem;
                margin: 1rem 0;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                cursor: pointer;
            }
            
            .button-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 35px rgba(0,0,0,0.15);
            }
            
            .admin-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            
            .client-card {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }
            
            .button-title {
                font-size: 1.8rem;
                font-weight: 600;
                color: white;
                margin-bottom: 0.5rem;
            }
            
            .button-description {
                font-size: 1rem;
                color: rgba(255, 255, 255, 0.9);
            }
            
            /* Feature box styling */
            .feature-box {
                background: #F9FAFB;
                border-left: 4px solid #3B82F6;
                padding: 1.5rem;
                margin: 1rem 0;
                border-radius: 8px;
            }
            
            /* Footer styling */
            .landing-footer {
                text-align: center;
                margin-top: 4rem;
                padding-top: 2rem;
                border-top: 1px solid #E5E7EB;
                color: #6B7280;
                font-size: 0.9rem;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Main container
        st.markdown('<div class="landing-container">', unsafe_allow_html=True)
        
        # Logo section
        self._render_logo()
        
        # Title and description
        self._render_header()
        
        # Navigation buttons
        self._render_navigation()
        
        # Features (optional)
        self._render_features()
        
        # Footer
        self._render_footer()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_logo(self):
        """Render company logo"""
        # Get the project root directory
        current_dir = Path(__file__).parent.parent.parent
        logo_path = current_dir / self.config['logo_path']
        
        if logo_path.exists():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(str(logo_path), use_container_width=True)
        else:
            st.warning(f"Logo not found at: {logo_path}")
    
    def _render_header(self):
        """Render title and description"""
        # Title
        st.markdown(
            f'<h1 class="main-title">{self.config["title"]}</h1>',
            unsafe_allow_html=True
        )
        
        # Tagline
        st.markdown(
            f'<div class="tagline">{self.config["tagline"]}</div>',
            unsafe_allow_html=True
        )
        
        # Description
        st.markdown(
            f'<div class="description">{self.config["description"]}</div>',
            unsafe_allow_html=True
        )
    
    def _render_navigation(self):
        """Render navigation buttons"""
        st.markdown("### Choose Your View")
        st.markdown("")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Admin button
            if st.button(
                self.config['admin_button_text'],
                key='admin_nav',
                use_container_width=True,
                type='primary'
            ):
                st.session_state.current_view = 'admin'
                st.session_state.show_landing = False
                st.rerun()
            
            st.markdown(
                f'<div class="button-description" style="text-align: center; margin-top: 0.5rem; color: #6B7280;">'
                f'{self.config["admin_button_description"]}</div>',
                unsafe_allow_html=True
            )
        
        with col2:
            # Client button
            if st.button(
                self.config['client_button_text'],
                key='client_nav',
                use_container_width=True,
                type='secondary'
            ):
                st.session_state.current_view = 'client'
                st.session_state.show_landing = False
                st.rerun()
            
            st.markdown(
                f'<div class="button-description" style="text-align: center; margin-top: 0.5rem; color: #6B7280;">'
                f'{self.config["client_button_description"]}</div>',
                unsafe_allow_html=True
            )
    
    def _render_features(self):
        """Render key features"""
        st.markdown("---")
        st.markdown("### Key Capabilities")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-box">
                <h4>🔍 Intelligent Querying</h4>
                <p>Ask natural language questions about occupations, industries, and workforce data</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-box">
                <h4>📊 Data Analytics</h4>
                <p>Computational analysis with aggregations, comparisons, and rankings</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-box">
                <h4>💡 Actionable Insights</h4>
                <p>AI-powered insights that drive smarter workforce decisions</p>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_footer(self):
        """Render footer"""
        st.markdown(
            '<div class="landing-footer">'
            'Powered by Advanced RAG Technology | Built with Streamlit, ChromaDB, and OpenAI'
            '</div>',
            unsafe_allow_html=True
        )
