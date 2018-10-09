@echo off
setlocal EnableDelayedExpansion
goto :init

:header
    echo %__NAME% v%__VERSION%
    echo This is a batch file to install an ilastik developement environment.
    echo.
    goto :eof

:usage
    echo USAGE:
    echo   %__BAT_NAME% [flags] "ENVIRONMENT_NAME" "ILASTIK-META_LOCAL_SOURCE_PATH"
    echo.
    echo.  -?, --help               show this help
    echo.  -v, --version            show the version
    echo.  -e, --verbose            show detailed output
    echo.  -s, --solvers            install ilastik with solvers
    echo.  -a, additional package   install additional package
    echo.  -c, conda channel        use additional conda channel (default: only conda-forge)
    goto :eof

:version
    if "%~1"=="full" call :header & goto :eof
    echo %__VERSION%
    goto :eof

:missing_argument
    call :header
    call :usage
    echo.
    echo ****                                   ****
    echo ****   No environment name specified   ****
    echo ****                                   ****
    echo.
    goto :eof

:init
    set "__NAME=%~n0"
    set "__VERSION=1"
    set "__YEAR=2018"

    set "__BAT_FILE=%~0"
    set "__BAT_PATH=%~dp0"
    set "__BAT_NAME=%~nx0"

    set "EnvName="
    set "IlastikMetaPath="
    set "BasePackage=ilastik-dependencies-no-solvers"
    set "Packages="
    set "Channels=-c conda-forge"

:parse
    if "%~1"=="" goto :validate

    if /i "%~1"=="/?"         call :header & call :usage "%~2" & goto :end
    if /i "%~1"=="-?"         call :header & call :usage "%~2" & goto :end
    if /i "%~1"=="--help"     call :header & call :usage "%~2" & goto :end

    if /i "%~1"=="/v"         call :version      & goto :end
    if /i "%~1"=="-v"         call :version      & goto :end
    if /i "%~1"=="--version"  call :version full & goto :end

    if /i "%~1"=="/e"         set "OptVerbose=yes"  & shift & goto :parse
    if /i "%~1"=="-e"         set "OptVerbose=yes"  & shift & goto :parse
    if /i "%~1"=="--verbose"  set "OptVerbose=yes"  & shift & goto :parse

    if /i "%~1"=="/s"         set "BasePackage=ilastik-dependencies"  & shift & goto :parse
    if /i "%~1"=="-s"         set "BasePackage=ilastik-dependencies"  & shift & goto :parse
    if /i "%~1"=="--solvers"  set "BasePackage=ilastik-dependencies"  & shift & goto :parse

    if /i "%~1"=="-a"         set "Packages=%Packages%%~2 "    & shift & shift & goto :parse
    if /i "%~1"=="-c"         set "Channels=%Channels% -c %~2" & shift & shift & goto :parse

    if not defined EnvName         set "EnvName=%~1"         & shift & goto :parse
    if not defined IlastikMetaPath set "IlastikMetaPath=%~1" & shift & goto :parse

    echo unknown argument: %~1
    call :header
    call :usage
    goto :end

:validate
    if not defined EnvName call :missing_argument & goto :end
    if defined IlastikMetaPath (
        set IlastikMetaPath=%IlastikMetaPath:/=\%
        if not exist %IlastikMetaPath% echo invalid path: %IlastikMetaPath% & goto :end
    )
:main
    if defined OptVerbose (
        echo **** DEBUG IS ON
        rem @echo on
    )
    set "Packages=%BasePackage% %Packages%"

                                   echo          new environment name: %EnvName%
                                   echo                using Channels: %Channels%
                                   echo           installing Packages: %Packages%

    if defined IlastikMetaPath     echo linking to existing directory: %IlastikMetaPath%
    if not defined IlastikMetaPath echo linking to existing directory: ILASTIK-META_LOCAL_SOURCE_PATH not provided


    if defined OptVerbose (echo activate conda root environment...)
    for /f "delims=" %%a in ('conda info --root') do @set CondaRoot=%%a
    call activate root
    if %errorlevel% neq 0 goto :end
    if defined OptVerbose (echo activate conda root environment done)

    if defined OptVerbose (echo creating conda environment...)
    @call conda create -y -n %EnvName% %Channels% %Packages%
    if %errorlevel% neq 0 goto :end
    if defined OptVerbose (echo creating conda environment done)

    if defined OptVerbose (if defined IlastikMetaPath echo removing ilastik-meta...)
    if defined IlastikMetaPath call conda remove -y -n %EnvName% ilastik-meta
    if %errorlevel% neq 0 goto :end
    if defined OptVerbose (if defined IlastikMetaPath echo removing ilastik-meta done)

    set EnvPrefix=%CondaRoot%\envs\%EnvName%
    if defined OptVerbose (if defined IlastikMetaPath echo creating symlink...)
    if defined IlastikMetaPath mklink /D "%EnvPrefix%\ilastik-meta" %IlastikMetaPath%
    if %errorlevel% neq 0 goto :end
    if defined OptVerbose (if defined IlastikMetaPath echo creating symlink done)

    if defined OptVerbose(echo writing custom ilastik-meta.pth...)
    (
      echo ../../ilastik-meta/lazyflow
      echo ../../ilastik-meta/volumina
      echo ../../ilastik-meta/ilastik
    ) > %EnvPrefix%\Lib\site-packages\ilastik-meta.pth
    if %errorlevel% neq 0 goto :end
    if defined OptVerbose(echo writing custom ilastik-meta.pth done)

    set "hasIlastikrc="
    if exist "%HOME%\.ilastikrc" set "hasIlastikrc=yes"

    if defined OptVerbose (
        if defined hasIlastikrc echo .ilastikrc found
        if not defined hasIlastikrc echo writing ilastikrc...
    )
    if not defined hasIlastikrc (
      echo [ilastik]
      echo debug: true
      echo plugin_directories: ~\.ilastik\plugins,
    ) > %HOME%\.ilastikrc
    if %errorlevel% neq 0 goto :end
    if defined OptVerbose (if not defined hasIlastikrc echo writing ilastikrc done)

:end
    call :cleanup
    exit /B %errorlevel%

:cleanup
    goto :eof
