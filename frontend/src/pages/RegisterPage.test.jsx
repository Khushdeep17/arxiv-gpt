import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import RegisterPage from "./RegisterPage";

// Mock useAuth
const mockRegister = jest.fn();
const mockUseAuth = jest.fn();

jest.mock("../context/AuthContext", () => ({
  useAuth: () => mockUseAuth(),
}));

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

describe("RegisterPage Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      register: mockRegister,
      isAuthenticated: false,
      loading: false,
    });
  });

  test("renders registration form with all inputs and links", () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: /create an account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^create account$/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /sign in/i })).toHaveAttribute("href", "/login");
  });

  test("validates password length min 8 characters", async () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password/i), {
      target: { value: "short" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "short" },
    });

    fireEvent.click(screen.getByRole("button", { name: /^create account$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/at least 8 characters/i);
    expect(mockRegister).not.toHaveBeenCalled();
  });

  test("validates password confirmation match", async () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password/i), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "mismatched123" },
    });

    fireEvent.click(screen.getByRole("button", { name: /^create account$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/passwords do not match/i);
    expect(mockRegister).not.toHaveBeenCalled();
  });

  test("submits valid registration and navigates to dashboard", async () => {
    mockRegister.mockResolvedValueOnce({
      user: { id: "u-2", email: "newuser@example.com", full_name: "Dr. Smith" },
    });

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/full name/i), {
      target: { value: "Dr. Smith" },
    });
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "newuser@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password/i), {
      target: { value: "securepassword123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "securepassword123" },
    });

    fireEvent.click(screen.getByRole("button", { name: /^create account$/i }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith(
        "newuser@example.com",
        "securepassword123",
        "Dr. Smith"
      );
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });

  test("surfaces 409 error when email already registered", async () => {
    mockRegister.mockRejectedValueOnce({
      response: { status: 409, data: { detail: "Email already registered" } },
    });

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "existing@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password/i), {
      target: { value: "securepassword123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "securepassword123" },
    });

    fireEvent.click(screen.getByRole("button", { name: /^create account$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/already exists/i);
  });
});

