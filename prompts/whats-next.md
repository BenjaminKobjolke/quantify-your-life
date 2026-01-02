<original_task>
Create a PHP 8.4 admin dashboard with Composer that:
1. Uses the XIDA login library (D:\GIT\Intern\ai-chat-api-php-login) for authentication
2. Presents forms for users to manage Matomo installation credentials
3. Stores form data in JSON using the login library's UserSettings API
4. Reuses build tools (SCSS compiler, JS minifier) from D:\wamp64\www\app-landing-page
5. Reuses Twig template patterns from app-landing-page
6. Displays Matomo visitor statistics with charts
7. Supports multiple users with separate configurations
</original_task>

<work_completed>
## Exploration Phase Complete

### 1. Login Library Analysis (D:\GIT\Intern\ai-chat-api-php-login)
- **Authentication methods**: Guest account creation, Google OAuth flow
- **Key classes**: XidaAuth, User, Credentials, UserSettings
- **Storage options**: FileStorage (JSON), SessionStorage, LaravelSessionStorage
- **UserSettings API**: saveObject(), loadObject() for JSON storage per user
- **Composer integration**: Local path repository, namespace `Xida\AiLogin\`
- **Documentation**: D:\GIT\Intern\ai-chat-api-php-login\docs\USER_SETTINGS.md

### 2. App-Landing-Page Build Tools Analysis (D:\wamp64\www\app-landing-page)
- **ScssCompiler** (src/Scss/ScssCompiler.php): PHP-based SCSS compilation with scssphp, on-demand with caching
- **JsMinifier** (src/Js/JsMinifier.php): PHP-based JS minification with matthiasmullie/minify
- **TwigFactory** (src/Template/TwigFactory.php): Custom Twig functions (asset, partial_css, partial_js, inline_css)
- **Container** (src/Container.php): Lazy-loading DI container pattern
- **Dependencies**: twig/twig ^3.22, scssphp/scssphp ^2.1, matthiasmullie/minify ^1.3

### 3. Matomo Statistics Analysis (D:\wamp64\www\matomo_statistics\index.php)
- **Required credentials**: site_url, username, app_password
- **API endpoint**: `{site}/index.php?rest_route=/matomo/v1/visits_summary/unique_visitors&period=month&date=last12`
- **Auth method**: HTTP Basic Auth via cURL (CURLAUTH_BASIC)
- **Response**: JSON array with monthly unique visitor counts

### 4. User Decisions Captured
- **Form library**: Symfony Form + Validator (full-featured with Twig integration)
- **Data storage**: UserSettings API (per-user, API-backed, synced across devices)
- **Charts**: ApexCharts (modern, real-time updates, dark theme support)
- **Multi-user**: Yes, each user has separate Matomo configurations

### 5. Plan File Created
- Location: C:\Users\XIDA\.claude\plans\dynamic-mapping-allen.md
- Contains: Directory structure, composer.json, component designs, implementation order
</work_completed>

<work_remaining>
## Phase 1: Foundation
1. Create directory structure in D:\wamp64\www\dashboard\
   ```
   mkdir -p public/assets/{css,js,images}
   mkdir -p src/{Controller,Service,Form/Type,Scss,Js,Template,Router}
   mkdir -p resources/{scss,js}
   mkdir -p templates/{auth,dashboard,matomo,statistics,components}
   mkdir -p config
   ```

2. Create composer.json with dependencies:
   - xida/ai-chat-api-php-login (local path: D:/GIT/Intern/ai-chat-api-php-login)
   - twig/twig ^3.22
   - symfony/form ^7.0, symfony/validator ^7.0, symfony/twig-bridge ^7.0
   - symfony/translation ^7.0, symfony/http-foundation ^7.0, symfony/security-csrf ^7.0
   - scssphp/scssphp ^2.1, matthiasmullie/minify ^1.3, guzzlehttp/guzzle ^7.0

3. Run `composer install`

4. Copy and adapt from app-landing-page:
   - src/Scss/ScssCompiler.php (change namespace App\Scss -> Dashboard\Scss, simplify site logic)
   - src/Js/JsMinifier.php (change namespace App\Js -> Dashboard\Js)

5. Create config/app.php with settings (software name, version, debug mode)

## Phase 2: Core Infrastructure
6. Create src/Container.php - simplified DI container (remove site/language services, add auth/form services)
7. Create src/Router/Router.php - simple URL routing
8. Create src/Template/TwigFactory.php - adapted (remove localization, add Symfony Form extension, auth globals)
9. Create public/index.php - front controller with routing
10. Create public/.htaccess - URL rewriting
11. Create templates/base.twig - base layout with ApexCharts CDN

## Phase 3: Authentication
12. Create src/Service/AuthService.php - wraps XidaAuth, manages SessionStorage
13. Create src/Controller/AbstractController.php - base with render(), redirect(), requireAuth()
14. Create src/Controller/AuthController.php - login, initiateOAuth, callback, logout
15. Create templates/auth/login.twig - login page with Google OAuth button

## Phase 4: Matomo Config CRUD
16. Create src/Service/MatomoConfigService.php - CRUD via UserSettings.saveObject/loadObject
17. Create src/Form/FormFactory.php - Symfony Form factory with Twig integration
18. Create src/Form/Type/MatomoConfigType.php - form type with validation constraints
19. Create src/Controller/MatomoConfigController.php - list, add, edit, delete actions
20. Create templates/matomo/list.twig - table with configs
21. Create templates/matomo/form.twig - add/edit form

## Phase 5: Statistics & Charts
22. Create src/Service/MatomoApiService.php - cURL client for Matomo REST API
23. Create src/Controller/StatisticsController.php - fetches data, prepares for charts
24. Create resources/js/charts.js - ApexCharts initialization (line + bar charts)
25. Create templates/statistics/view.twig - charts page with config selector

## Phase 6: Styling
26. Create resources/scss/_variables.scss - color scheme, fonts
27. Create resources/scss/_components.scss - buttons, cards, forms, tables
28. Create resources/scss/_dashboard.scss - dashboard-specific styles
29. Create resources/scss/style.scss - main entry importing partials
30. Create templates/components/navbar.twig, flash-messages.twig
31. Create templates/dashboard/index.twig - main dashboard home
</work_remaining>

<attempted_approaches>
## Research Completed (No Failures)

### Form Libraries Evaluated
1. **Symfony Form + Validator** - SELECTED: Full-featured, excellent Twig integration, PHP 8.4 compatible
2. **PHP Form Builder Pro** - Rejected: Commercial, less validation integration
3. **Custom forms** - Rejected: Too basic for multi-field validation needs

### Charting Libraries Evaluated
1. **Chart.js** - Considered: Lightweight, popular, but fewer features
2. **ApexCharts** - SELECTED: Modern, real-time updates, better dark theme support
3. **CanvasJS** - Considered: Fast but free version has limitations

### Storage Options Evaluated
1. **UserSettings API** - SELECTED: Per-user, API-backed, syncs across devices
2. **FileStorage** - Rejected: Local-only, not portable between sessions
3. **Database** - Not available: Would require additional setup

### No Errors or Blockers Encountered
- All explored projects are accessible and readable
- All required dependencies are available via Composer
- Login library supports all needed functionality
</attempted_approaches>

<critical_context>
## Key Decisions

1. **Single-site architecture**: Unlike app-landing-page which supports multiple sites, this dashboard is single-site. Remove site detection and fallback logic from copied files.

2. **Symfony Form standalone**: Using Symfony Form outside Symfony framework requires:
   - symfony/twig-bridge for form rendering
   - symfony/translation for labels
   - symfony/security-csrf for CSRF protection
   - Manual FormFactory setup (not autowired)

3. **UserSettings JSON schema**:
   ```json
   {
     "configs": [{"id": "uuid", "name": "", "site_url": "", "username": "", "app_password": "", "created_at": "", "updated_at": ""}],
     "default_config_id": "uuid"
   }
   ```

4. **Matomo API authentication**: Uses HTTP Basic Auth, NOT token-based. Password is app_password from Matomo settings.

5. **ApexCharts via CDN**: `https://cdn.jsdelivr.net/npm/apexcharts` - no npm/node required

## Important File Paths

| Purpose | Path |
|---------|------|
| Login library | D:\GIT\Intern\ai-chat-api-php-login |
| Build tools source | D:\wamp64\www\app-landing-page\src\ |
| Matomo API reference | D:\wamp64\www\matomo_statistics\index.php |
| New dashboard | D:\wamp64\www\dashboard\ |
| Plan file | C:\Users\XIDA\.claude\plans\dynamic-mapping-allen.md |

## Environment Notes
- Platform: Windows (wamp64)
- PHP version: 8.4 required
- No git repo initialized in dashboard folder
- Base path calculation needed for subdirectory deployment

## Gotchas to Watch

1. **Namespace changes**: When copying ScssCompiler.php and JsMinifier.php, change `App\` to `Dashboard\`

2. **TwigFactory adaptation**: Remove `Localization` parameter, add `FormExtension` from symfony/twig-bridge

3. **Session handling**: Call `session_start()` before using SessionStorage

4. **Password on edit**: MatomoConfigType should make app_password optional when editing (keep existing if blank)

5. **SSL verification**: Matomo API calls may need SSL verification disabled for development (like in matomo_statistics/index.php)
</critical_context>

<current_state>
## Status: Planning Complete, Ready for Implementation

### Deliverables Status
| Item | Status |
|------|--------|
| Requirements gathered | Complete |
| User decisions captured | Complete |
| Codebase exploration | Complete |
| Implementation plan | Complete |
| Plan file written | Complete |
| Directory structure | Not started |
| Code implementation | Not started |

### Plan Mode
- Currently in plan mode (cannot make edits except to plan file)
- Plan file created at: C:\Users\XIDA\.claude\plans\dynamic-mapping-allen.md
- Ready to call ExitPlanMode for user approval

### Open Questions (None)
All user decisions have been captured:
- Form library: Symfony Form + Validator
- Storage: UserSettings API
- Charts: ApexCharts
- Multi-user: Yes

### Next Immediate Action
Call ExitPlanMode to get user approval, then begin Phase 1 implementation (directory structure + composer.json).
</current_state>
