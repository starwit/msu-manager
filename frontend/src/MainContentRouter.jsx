import { Route, Routes } from "react-router-dom";
import LandingLayout from "./app/commons/LandingLayout";
import LandingPage from "./app/features/landing/LandingPage";

function MainContentRouter() {
    return (
        <Routes>
            <Route path="/" element={<LandingLayout><LandingPage /></LandingLayout>} />
            <Route path="/logout" component={() => {
                window.location.href = window.location.pathname + "api/user/logout";
                return null;
            }} />
        </Routes>
    );
}

export default MainContentRouter;
