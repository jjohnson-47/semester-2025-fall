# Blackboard Ultra HTML documentation verification report

Based on comprehensive research of official Blackboard documentation as of August 24-25, 2025, this report verifies the current technical specifications for HTML and content parameters in Blackboard Ultra. The research confirms most claims from your document, with one critical update regarding app versions.

## Verification status of specific claims

### **HTML stripping in mobile apps: CONFIRMED ✅**

Official Blackboard documentation explicitly states that **HTML tags in titles, content names, and description fields are filtered out and not displayed** in mobile apps. This is an intentional design decision documented in their "Supported HTML in Mobile Apps" guide. The stripping applies to assignment names, announcement subjects, and content titles, where only plain text is supported. However, full HTML support exists within content areas themselves, including bold, italic, tables, iframes, embedded images, and HTML5 video.

### **Alternate domain requirement for custom HTML blocks: CONFIRMED ✅**

The requirement for an alternate domain is **mandatory, not optional**. Official documentation unequivocally states that institutions must have an alternate domain configured for custom HTML/CSS blocks to function. This configuration is managed through the Admin Panel's Security settings and implements a defense-in-depth security model. Without this configuration, the "Add HTML" option simply won't appear in Ultra Documents.

### **Iframe containment for security: CONFIRMED ✅**

Custom HTML blocks are definitively contained within iframes as a security measure. When HTML content loads in read-only mode, it's served from the alternate domain in an iframe, creating complete isolation from the main Blackboard session. This architecture prevents session hijacking attacks and leverages the browser's same-origin policy to compartmentalize potentially malicious scripts.

### **Version numbers cited: OUTDATED ❌**

**Critical finding**: The Blackboard Instructor app was **discontinued in September 2022**. The version numbers "Blackboard app 3.5+" and "Instructor 1.7+" reference legacy applications that no longer exist. As of August 2025, Blackboard uses a **single unified app (version 10.5.0)** for both students and instructors. Any documentation referencing separate apps is approximately three years outdated.

## Mobile-friendly content best practices in Ultra Course View

Current official guidelines emphasize structural optimization over HTML complexity. Best practices include limiting folder depth to reduce scrolling, using concise titles that display well on small screens, and grouping content strategically across multiple areas rather than single folders. The documentation recommends testing with mock student accounts early in development and focusing on file types with universal mobile support.

For mobile rendering, instructors should plan courses using plain text for all titles and names while leveraging full HTML capabilities within content areas. The system supports responsive breakpoints that automatically convert multi-column layouts to single columns and maintains aspect ratios for all media elements.

## Supported HTML and CSS elements in mobile apps

The official documentation confirms **full HTML support** within content areas for:
- Text formatting (bold, italic, underline, strikethrough)
- Structural elements (paragraphs, DIV, line breaks)
- Lists (bulleted and numbered)
- Tables and iframes
- Embedded images and HTML5 video
- YouTube mashups and multimedia embeds
- Text colors, sizes, and background highlighting
- Alignment and horizontal rules

However, this support applies **only to content areas**, not to titles or navigation elements where HTML is systematically stripped for consistency and performance.

## Custom HTML/CSS blocks implementation details

Ultra Documents implement custom HTML through a sophisticated architecture involving BbML (Blackboard Markup Language) encoding and a CodeEditor package that standardizes third-party editor configurations. The system requires specific role permissions ("Add/Edit embedded content with scripts into iframe") and implements Safe HTML filtering using OWASP's AntiSamy API for XSS protection.

The alternate domain serves content exclusively through WebDAV requests and cannot be used for normal Blackboard functions. All content forwarding from the primary to alternate domain happens transparently, maintaining the user experience while ensuring security isolation.

## Ultra Documents responsive layout features

Ultra Documents provide enterprise-grade responsive design with automatic media resizing that maintains aspect ratios, center alignment, and maximum width constraints. The system implements intelligent column-to-row conversion for mobile displays and supports inline rendering for Office files through on-demand PDF conversion.

Documents support various block types including content blocks, HTML blocks, knowledge check blocks, and multimedia blocks. Each type has specific rendering rules optimized for different screen sizes. The platform enforces curated design elements with accessible color palettes and standardized font families to ensure consistency across devices.

## HTML parameters and restrictions for optimal rendering

Blackboard Ultra enforces specific constraints to balance flexibility with security and accessibility. Text colors are limited to an accessible palette (black, gray, purple, blue, green), and unsupported colors automatically convert to black. Font choices are curated to include web-safe options with Open Sans as the universal fallback.

The system doesn't support anchor navigation within documents and removes certain advanced CSS properties that could interfere with responsive design. File upload limits and character restrictions (750 for descriptions) ensure optimal performance across all platforms.

## Conclusion

The verification confirms that Blackboard Ultra implements robust HTML support with clearly documented security boundaries. The key distinction between content areas (full HTML support) and navigation elements (plain text only) represents an intentional design choice balancing functionality with mobile performance. The mandatory alternate domain requirement and iframe containment demonstrate enterprise-level security architecture. Organizations should update any documentation referencing the discontinued Instructor app to reflect the current unified application model introduced in 2022.
