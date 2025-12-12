import {AppBar, Container, IconButton, Stack, Toolbar, Typography} from "../../../node_modules/@mui/material";
import CustomFooter from "./CustomFooter";

import general from "../assets/images/logo_color.png";

function Layout({children}) {
    const themeMap = {general};
    const DynamicLogo = themeMap["general"];

    return (
        <>
            <Container>
                <AppBar color="secondary">
                    <Toolbar>
                        <Stack
                            direction="row"
                            sx={{justifyContent: "center", alignItems: "center", width: "100%"}}
                        >
                            <IconButton
                                size="large"
                                edge="start"
                                color="inherit"
                                href="./"
                                aria-label="menu"
                                sx={{margin: 0, padding: 0, marginRight: 2}}
                            >
                                <img src={DynamicLogo} height={40} alt="MSU Manager" />
                            </IconButton>
                            <Typography variant="h1" component="div" noWrap>
                                MSU Manager
                            </Typography>
                        </Stack>
                    </Toolbar>
                </AppBar>
            </Container >
            <Container sx={{paddingTop: "5em", paddingBottom: "4em"}}>
                {children}
            </Container >
            <CustomFooter />
        </>
    );
};

export default Layout;